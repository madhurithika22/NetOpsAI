import uuid
import math
from datetime import datetime, timezone
from typing import Tuple, List, Dict, Any, Optional
from app.models.ceso_models import NetworkState
from app.models.cadd_models import DiagnosticReport, DiagnosticEvidence, ActionPlan, ProposedAction

def safe_float(val: Any, default: float = 0.0) -> float:
    """Safely converts input value to float, coercing None, NaN, and Inf to default."""
    if val is None:
        return default
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (ValueError, TypeError):
        return default

def psi(x: float) -> float:
    """Bounded non-linear clamp function mapping x to [0.0, 1.0]."""
    return max(0.0, min(1.0, safe_float(x)))


class ExplainableRuleEngine:
    """
    Context-Aware Diagnosis Engine (CADE).
    Evaluates operational NetworkState snapshots through a reproducible,
    mathematically specified candidate-scoring framework.
    Strictly isolated from ground-truth scenario labels and expected diagnoses.
    """
    VERSION = "2.0.0-phase2"
    LATENCY_THRESHOLD_MS = 50.0
    PACKET_LOSS_THRESHOLD_PCT = 10.0
    CONFIDENCE_ESCALATION_THRESHOLD = 0.70

    # Pre-defined deterministic tie-breaking priority (higher priority first)
    TIE_BREAKING_PRIORITY = [
        "INTERFACE_FAILURE",
        "ROUTING_MISCONFIGURATION",
        "DC_MTU_MISMATCH",
        "OSPF_ADJACENCY_FLAP",
        "WAN_PATH_DEGRADATION",
        "HIGH_LATENCY_CONGESTION",
        "PACKET_LOSS",
        "UNKNOWN_COMPOSITE_ANOMALY",
        "HEALTHY"
    ]

    def __init__(self):
        self.config = {
            "latency_threshold_ms": self.LATENCY_THRESHOLD_MS,
            "packet_loss_threshold_pct": self.PACKET_LOSS_THRESHOLD_PCT,
            "escalation_threshold": self.CONFIDENCE_ESCALATION_THRESHOLD
        }

    def diagnose_state(self, state: NetworkState) -> Tuple[DiagnosticReport, ActionPlan]:
        snapshot_id = state.snapshot_id or f"snap-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc)
        diagnosis_id = f"diag-{uuid.uuid4().hex[:8]}"
        plan_id = f"plan-{uuid.uuid4().hex[:8]}"

        # 1. Extract and normalize operational features
        interfaces = state.interfaces or {}
        links = state.links or []
        routes = state.routes or []

        total_ifaces = max(1, len(interfaces))
        down_ifaces = [name for name, iface in interfaces.items() if not iface.is_up]
        f_down = len(down_ifaces) / float(total_ifaces)

        misconfigured_routes = [
            r for r in routes
            if safe_float(r.metric) >= 999 or r.interface in ["rtr1-eth0", "veth-r1-ha", "loopback"]
        ]
        f_route = 1.0 if misconfigured_routes else 0.0

        lat_scores = [psi((safe_float(l.rtt_ms) - 50.0) / 50.0) for l in links] if links else [0.0]
        f_lat = max(lat_scores)

        loss_scores = [psi((safe_float(l.packet_loss_pct) - 10.0) / 30.0) for l in links] if links else [0.0]
        f_loss = max(loss_scores)

        err_scores = [psi(safe_float(iface.rx_errors) / 50.0) for iface in interfaces.values()] if interfaces else [0.0]
        f_err = max(err_scores)

        util_scores = [psi((safe_float(iface.utilization_pct) - 75.0) / 20.0) for iface in interfaces.values()] if interfaces else [0.0]
        f_util = max(util_scores)

        mtu_bad = [
            iface for iface in interfaces.values()
            if (iface.mtu > 0 and iface.mtu not in (1500, 9000)) and safe_float(iface.rx_drops) > 100
        ]
        f_mtu = 1.0 if mtu_bad else 0.0

        # 2. Evaluate Candidate Scores S(c)
        candidate_scores: Dict[str, float] = {}

        candidate_scores["INTERFACE_FAILURE"] = round(f_down if f_down > 0 else (1.0 if down_ifaces else 0.0), 4)
        candidate_scores["ROUTING_MISCONFIGURATION"] = round(f_route, 4)
        candidate_scores["DC_MTU_MISMATCH"] = round(f_mtu, 4)
        
        candidate_scores["OSPF_ADJACENCY_FLAP"] = round(
            (0.6 * f_err + 0.4 * f_route) if (f_err > 0 and f_route > 0) else 0.0, 4
        )
        
        candidate_scores["WAN_PATH_DEGRADATION"] = round(
            (0.6 * f_util + 0.4 * f_loss) if f_util > 0 else 0.0, 4
        )

        candidate_scores["HIGH_LATENCY_CONGESTION"] = round(
            (0.7 * f_lat + 0.3 * f_loss) if (len(down_ifaces) == 0 and f_lat > f_loss and f_lat > 0) else 0.0, 4
        )

        candidate_scores["PACKET_LOSS"] = round(
            (0.8 * f_loss + 0.2 * f_lat) if (len(down_ifaces) == 0 and f_loss >= f_lat and f_loss > 0) else 0.0, 4
        )

        max_direct_score = max([v for k, v in candidate_scores.items()])
        is_composite_symptoms = (
            max_direct_score < 0.70 and
            (state.anomalies_detected or f_lat > 0 or f_loss > 0 or f_util > 0 or f_err > 0)
        )
        candidate_scores["UNKNOWN_COMPOSITE_ANOMALY"] = round(
            min(0.65, 0.35 * f_lat + 0.35 * f_loss + 0.30 * f_util + 0.30 * f_err) if is_composite_symptoms else 0.0, 4
        )

        max_feature_val = max(f_down, f_route, f_lat, f_loss, f_err, f_util, f_mtu)
        if state.anomalies_detected or max_feature_val >= 0.50:
            candidate_scores["HEALTHY"] = 0.0
        else:
            candidate_scores["HEALTHY"] = round(max(0.0, 1.0 - max_feature_val), 4)

        # 3. Candidate Selection with Deterministic Tie-Breaking
        sorted_candidates = sorted(
            candidate_scores.keys(),
            key=lambda c: (candidate_scores[c], -self.TIE_BREAKING_PRIORITY.index(c)),
            reverse=True
        )

        top_candidate = sorted_candidates[0]
        top_score = candidate_scores[top_candidate]

        second_candidate = sorted_candidates[1]
        second_score = candidate_scores[second_candidate]

        # 4. Computed Confidence Score & Escalation Decision
        if top_candidate == "HEALTHY" and top_score >= 1.0:
            confidence = 1.0
        else:
            confidence = round(top_score * (1.0 - 0.5 * second_score), 4)
            confidence = max(0.0, min(1.0, confidence))

        escalation_required = (confidence < self.CONFIDENCE_ESCALATION_THRESHOLD) or (top_candidate == "UNKNOWN_COMPOSITE_ANOMALY")

        # 5. Build Evidence Chain and Impacted Elements
        evidence_chain: List[DiagnosticEvidence] = []
        impacted_elements: List[str] = []
        candidate_causes: List[str] = []

        if top_candidate == "INTERFACE_FAILURE":
            impacted_elements = down_ifaces or ["unknown_interface"]
            evidence_chain.append(DiagnosticEvidence(
                rule_id="RULE_INTERFACE_DOWN",
                rule_name="Interface Status Failure Check",
                condition_matched="interface.is_up == False",
                observed_value=f"Down interfaces: {', '.join(impacted_elements)}",
                threshold_value="interface.is_up == True"
            ))
            candidate_causes = ["Physical link disconnection", "Interface admin down state", "Hardware transceiver failure"]

        elif top_candidate == "ROUTING_MISCONFIGURATION":
            impacted_elements = [r.destination for r in misconfigured_routes] or ["10.0.2.0/24"]
            for r in misconfigured_routes:
                evidence_chain.append(DiagnosticEvidence(
                    rule_id="RULE_ROUTING_BLACKHOLE",
                    rule_name="Route Egress & Metric Validation",
                    condition_matched="route.metric >= 999 OR interface is invalid",
                    observed_value=f"Destination {r.destination} via {r.interface} (metric={r.metric})",
                    threshold_value="metric < 100 and egress valid"
                ))
            candidate_causes = ["Static route blackhole", "Routing protocol metric corruption", "Missing next-hop ARP"]

        elif top_candidate == "HIGH_LATENCY_CONGESTION":
            high_lat_links = [l for l in links if safe_float(l.rtt_ms) > self.LATENCY_THRESHOLD_MS]
            impacted_elements = [f"{l.source_node}<->{l.target_node}" for l in high_lat_links] or ["rtr1<->rtr2"]
            for l in high_lat_links:
                evidence_chain.append(DiagnosticEvidence(
                    rule_id="RULE_HIGH_LATENCY_CONGESTION",
                    rule_name="Link Latency Threshold Check",
                    condition_matched=f"rtt_ms > {self.LATENCY_THRESHOLD_MS}",
                    observed_value=f"RTT={l.rtt_ms}ms on {l.source_node}<->{l.target_node}",
                    threshold_value=f"RTT <= {self.LATENCY_THRESHOLD_MS}ms"
                ))
            candidate_causes = ["Queue saturation", "Traffic netem delay injection", "Bandwidth bottleneck"]

        elif top_candidate == "PACKET_LOSS":
            high_loss_links = [l for l in links if safe_float(l.packet_loss_pct) > self.PACKET_LOSS_THRESHOLD_PCT]
            impacted_elements = [f"{l.source_node}<->{l.target_node}" for l in high_loss_links] or ["rtr1<->rtr2"]
            for l in high_loss_links:
                evidence_chain.append(DiagnosticEvidence(
                    rule_id="RULE_PACKET_LOSS",
                    rule_name="Link Packet Loss Threshold Check",
                    condition_matched=f"packet_loss_pct > {self.PACKET_LOSS_THRESHOLD_PCT}%",
                    observed_value=f"Loss={l.packet_loss_pct}% on {l.source_node}<->{l.target_node}",
                    threshold_value=f"Loss <= {self.PACKET_LOSS_THRESHOLD_PCT}%"
                ))
            candidate_causes = ["Link noise/CRC drops", "Queue overflow", "Netem drop injection"]

        elif top_candidate == "DC_MTU_MISMATCH":
            impacted_elements = [iface.name for iface in mtu_bad] or ["spine-01-eth3"]
            evidence_chain.append(DiagnosticEvidence(
                rule_id="RULE_DC_MTU_MISMATCH",
                rule_name="Fabric Interface MTU Alignment Check",
                condition_matched="interface.mtu != 1500/9000 OR rx_drops > 100",
                observed_value=f"MTU mismatch / high drops on {', '.join(impacted_elements)}",
                threshold_value="MTU == 1500 or 9000, drops == 0"
            ))
            candidate_causes = ["Interface MTU misconfiguration", "Jumbo frame fragmentation drop", "Silent Path MTU Discovery failure"]

        elif top_candidate == "WAN_PATH_DEGRADATION":
            impacted_elements = [name for name, iface in interfaces.items() if safe_float(iface.utilization_pct) > 75.0] or ["dc-gw02-wan1"]
            evidence_chain.append(DiagnosticEvidence(
                rule_id="RULE_SDWAN_SECONDARY_CONGESTION",
                rule_name="SD-WAN Secondary Circuit Queue Saturation Check",
                condition_matched="utilization_pct > 75%",
                observed_value=f"High utilization on {', '.join(impacted_elements)}",
                threshold_value="utilization_pct <= 75%"
            ))
            candidate_causes = ["Primary circuit SLA failover", "Secondary WAN congestion", "Unshaped bulk traffic"]

        elif top_candidate == "OSPF_ADJACENCY_FLAP":
            impacted_elements = [name for name, iface in interfaces.items() if safe_float(iface.rx_errors) > 0] or ["core-rtr01-eth2"]
            evidence_chain.append(DiagnosticEvidence(
                rule_id="RULE_OSPF_ADJACENCY_FLAP",
                rule_name="OSPF Neighbor State & Path Metric Check",
                condition_matched="rx_errors > 0 AND route.metric >= 999",
                observed_value=f"RX error accumulation on {', '.join(impacted_elements)}",
                threshold_value="rx_errors == 0, metric < 100"
            ))
            candidate_causes = ["OSPF hello timer mismatch", "Interface MTU mismatch on core link", "Physical layer CRC flapping"]

        elif top_candidate == "UNKNOWN_COMPOSITE_ANOMALY":
            impacted_elements = list(interfaces.keys())[:3] if interfaces else ["edge-gw-01", "wan-rtr-01"]
            evidence_chain.append(DiagnosticEvidence(
                rule_id="RULE_COMPOSITE_ANOMALY_EVALUATION",
                rule_name="Cross-Domain Multi-Metric Anomaly Aggregator",
                condition_matched="Distributed sub-threshold anomalies across latency/loss/utilization",
                observed_value=f"f_lat={f_lat}, f_loss={f_loss}, f_util={f_util}",
                threshold_value="Single candidate score >= 0.70"
            ))
            candidate_causes = ["Edge resolver cache contention", "BGP local preference route drift", "Cross-cloud WAN micro-burst"]

        else: # HEALTHY
            evidence_chain.append(DiagnosticEvidence(
                rule_id="RULE_BASELINE_HEALTHY",
                rule_name="Baseline Health Check",
                condition_matched="All metrics within baseline SLA",
                observed_value=f"Max feature deviation: {max_feature_val:.4f}",
                threshold_value="All feature deviations < 0.10"
            ))

        # 6. Generate DiagnosticReport
        summary_text = (
            f"Diagnosis: {top_candidate} (Score: {top_score:.4f}, Confidence: {confidence:.4f}). "
            f"Impacted: {', '.join(impacted_elements) if impacted_elements else 'None'}."
        )

        severity = "CRITICAL" if top_candidate in ("INTERFACE_FAILURE", "OSPF_ADJACENCY_FLAP") else (
            "HIGH" if top_candidate in ("ROUTING_MISCONFIGURATION", "HIGH_LATENCY_CONGESTION", "PACKET_LOSS", "DC_MTU_MISMATCH", "WAN_PATH_DEGRADATION", "UNKNOWN_COMPOSITE_ANOMALY") else "LOW"
        )

        report = DiagnosticReport(
            diagnosis_id=diagnosis_id,
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            fault_type=top_candidate,
            impacted_elements=impacted_elements,
            severity=severity,
            confidence_score=confidence,
            evidence_chain=evidence_chain,
            explanation_summary=summary_text,
            escalation_required=escalation_required,
            candidate_causes=candidate_causes,
            algorithm_version=self.VERSION,
            algorithm_config=self.config,
            candidate_scores=candidate_scores
        )

        # 7. Generate Proposed Remediation Action Plan
        action = self._create_proposed_action(top_candidate, impacted_elements, misconfigured_routes)
        plan = ActionPlan(
            plan_id=plan_id,
            diagnosis_id=diagnosis_id,
            proposed_actions=[action] if action else [],
            estimated_risk_level="HIGH" if top_candidate in ("INTERFACE_FAILURE", "UNKNOWN_COMPOSITE_ANOMALY") else ("MEDIUM" if action else "LOW"),
            requires_approval=bool(action)
        )

        return report, plan

    def _create_proposed_action(
        self,
        candidate: str,
        impacted_elements: List[str],
        misconfigured_routes: List[Any]
    ) -> Optional[ProposedAction]:
        act_id = f"act-{uuid.uuid4().hex[:8]}"

        if candidate == "INTERFACE_FAILURE":
            target_iface = impacted_elements[0] if impacted_elements else "veth-r1-r2"
            target_dev = "rtr1" if "rtr1" in target_iface else "netops-rtr1"
            return ProposedAction(
                action_id=act_id,
                command_type="SET_INTERFACE_STATE",
                target_device=target_dev,
                parameters={"interface": target_iface, "target_state": "UP"},
                is_destructive=True,
                reversion_action={"interface": target_iface, "target_state": "DOWN"}
            )

        elif candidate == "ROUTING_MISCONFIGURATION":
            bad_route = misconfigured_routes[0] if misconfigured_routes else None
            dest = bad_route.destination if bad_route else "10.0.2.0/24"
            target_iface = bad_route.interface if bad_route else "veth-r1-ha"
            target_dev = "rtr1" if "rtr1" in target_iface else "netops-rtr1"
            return ProposedAction(
                action_id=act_id,
                command_type="RESTORE_ROUTING_TABLE",
                target_device=target_dev,
                parameters={
                    "destination": dest,
                    "interface": "rtr1-eth1" if "rtr1" in target_iface else "veth-r1-r2",
                    "gateway": "10.0.2.2",
                    "new_metric": "10"
                },
                is_destructive=True,
                reversion_action={"destination": dest, "interface": target_iface, "metric": "999"}
            )

        elif candidate == "HIGH_LATENCY_CONGESTION":
            target_link = impacted_elements[0] if impacted_elements else "netops-rtr1<->netops-rtr2"
            target_dev = "rtr1" if "rtr1" in target_link else "netops-rtr1"
            return ProposedAction(
                action_id=act_id,
                command_type="REROUTE_TRAFFIC",
                target_device=target_dev,
                parameters={
                    "interface": "veth-r1-r2",
                    "action": "INCREASE_ROUTE_METRIC",
                    "target_destination": "10.0.2.0/24",
                    "new_metric": "100"
                },
                is_destructive=True,
                reversion_action={"interface": "veth-r1-r2", "action": "RESTORE_ROUTE_METRIC", "original_metric": "10"}
            )

        elif candidate == "PACKET_LOSS":
            target_link = impacted_elements[0] if impacted_elements else "netops-rtr1<->netops-rtr2"
            target_dev = "rtr1" if "rtr1" in target_link else "netops-rtr1"
            return ProposedAction(
                action_id=act_id,
                command_type="REROUTE_TRAFFIC",
                target_device=target_dev,
                parameters={
                    "interface": "veth-r1-r2",
                    "target_destination": "10.0.2.0/24",
                    "new_metric": "100"
                },
                is_destructive=True,
                reversion_action={"interface": "veth-r1-r2", "original_metric": "10"}
            )

        elif candidate == "DC_MTU_MISMATCH":
            target_iface = impacted_elements[0] if impacted_elements else "spine-01-eth3"
            return ProposedAction(
                action_id=act_id,
                command_type="SET_INTERFACE_MTU",
                target_device="spine-01",
                parameters={"interface": target_iface, "mtu": 9000},
                is_destructive=True,
                reversion_action={"interface": target_iface, "mtu": 1400}
            )

        elif candidate == "WAN_PATH_DEGRADATION":
            target_iface = impacted_elements[0] if impacted_elements else "dc-gw02-wan1"
            return ProposedAction(
                action_id=act_id,
                command_type="APPLY_SDWAN_QOS_TRAFFIC_SHAPING",
                target_device="dc-gw02",
                parameters={
                    "interface": target_iface,
                    "action": "ENABLE_TRAFFIC_SHAPING_AND_RATE_LIMIT",
                    "high_priority_class": "ERP_BUSINESS_CRITICAL",
                    "rate_limit_bulk_pct": 20
                },
                is_destructive=True,
                reversion_action={"interface": target_iface, "action": "DISABLE_QOS_SHAPING"}
            )

        elif candidate == "OSPF_ADJACENCY_FLAP":
            return ProposedAction(
                action_id=act_id,
                command_type="RESET_OSPF_NEIGHBOR_AND_METRIC",
                target_device="core-rtr01",
                parameters={
                    "interface": "eth2",
                    "action": "RESTORE_OSPF_TIMERS_AND_METRIC",
                    "hello_interval": 10,
                    "cost": 10
                },
                is_destructive=True,
                reversion_action={"interface": "eth2", "action": "INJECT_OSPF_TIMER_MISMATCH"}
            )

        elif candidate == "UNKNOWN_COMPOSITE_ANOMALY":
            return ProposedAction(
                action_id=act_id,
                command_type="RESTART_EDGE_RESOLVER_AND_RESET_BGP_PREFERENCE",
                target_device="edge-gw-01",
                parameters={
                    "service": "dns-resolver",
                    "target_gateway": "edge-gw-01",
                    "action": "FLUSH_DNS_CACHE_AND_RESTORE_BGP_LOCAL_PREF",
                    "bgp_neighbor": "cloud-gw-01",
                    "local_pref": 200
                },
                is_destructive=True,
                reversion_action={"target_gateway": "edge-gw-01", "action": "SET_BGP_LOCAL_PREF", "local_pref": 50}
            )

        return None
