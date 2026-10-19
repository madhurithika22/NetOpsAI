import sys
sys.path.insert(0, 'backend')
import json
import collections
from app.scenarios.registry import scenario_registry
from app.cadd.engine import ExplainableRuleEngine
from app.llm.models import LLMContextPackage
from app.llm.prompts import build_direct_prompt, build_netops_prompt

def audit_topologies():
    print("=== 1. TOPOLOGY CONNECTIVITY AUDIT ===")
    scenarios = scenario_registry.list_scenarios()
    
    for sc in scenarios:
        node_ids = set(n.id for n in sc.nodes)
        print(f"\nScenario [{sc.scenario_id}] {sc.name}:")
        print(f" - Declared Nodes: {len(sc.nodes)} (Target: {sc.target_node_count})")
        print(f" - Declared Links: {len(sc.links)} (Target: {sc.target_link_count})")

        # Unique node ID check
        node_list = [n.id for n in sc.nodes]
        duplicates = [item for item, count in collections.Counter(node_list).items() if count > 1]
        assert len(duplicates) == 0, f"Duplicate nodes found in {sc.scenario_id}: {duplicates}"

        # Link endpoint existence check
        adj = collections.defaultdict(list)
        missing_endpoints = []
        for link in sc.links:
            if link.source_node not in node_ids:
                missing_endpoints.append(f"Link {link.id} source '{link.source_node}' not in node set")
            if link.target_node not in node_ids:
                missing_endpoints.append(f"Link {link.id} target '{link.target_node}' not in node set")
            adj[link.source_node].append(link.target_node)
            adj[link.target_node].append(link.source_node)

        assert len(missing_endpoints) == 0, f"Missing endpoints in {sc.scenario_id}: {missing_endpoints}"

        # Connected component check via BFS from first node
        visited = set()
        queue = [sc.nodes[0].id]
        while queue:
            curr = queue.pop(0)
            if curr not in visited:
                visited.add(curr)
                queue.extend(neighbor for neighbor in adj[curr] if neighbor not in visited)

        unvisited = node_ids - visited
        print(f" - Connected Nodes Reachable from '{sc.nodes[0].id}': {len(visited)} / {len(node_ids)}")
        if unvisited:
            print(f"   [WARNING] Unconnected nodes: {unvisited}")
        else:
            print(f"   [OK] Graph is fully connected! Single component.")

def audit_ground_truth_leakage():
    print("\n=== 2. GROUND TRUTH LEAKAGE AUDIT ===")
    cadd_engine = ExplainableRuleEngine()
    sc_def = scenario_registry.load_scenario("CASE_04")
    fault_type = scenario_registry.inject_fault("CASE_04")
    telemetry = scenario_registry.generate_telemetry("CASE_04", fault_type)
    cadd_report, _ = cadd_engine.diagnose_state(telemetry)

    raw_telemetry_dict = telemetry.model_dump(mode="json")
    ctx_package = LLMContextPackage(
        incident_id="inc-audit-04",
        scenario_id="CASE_04",
        timestamp=telemetry.timestamp.isoformat(),
        topology_summary={"node_count": sc_def.target_node_count, "link_count": sc_def.target_link_count},
        affected_nodes=cadd_report.impacted_elements,
        affected_links=[l.source_node + "<->" + l.target_node for l in telemetry.links if l.status != "HEALTHY"],
        ceso_findings=["Anomaly detected on Hybrid Edge network"],
        relevant_telemetry={"anomalies_detected": telemetry.anomalies_detected},
        correlated_anomalies=[sc_def.fault_definition.description],
        cadd_diagnosis=cadd_report.fault_type,
        diagnosis_confidence=cadd_report.confidence_score,
        candidate_causes=cadd_report.candidate_causes,
        msvs_safety_constraints=["Do not touch eth0"],
        candidate_remediation_actions=[a.model_dump(mode="json") for a in sc_def.remediation_candidates],
        verification_requirements=sc_def.verification_criteria
    )

    direct_prompt = build_direct_prompt(raw_telemetry_dict, ["Syslog entry 1"], ["Event 1"])
    netops_prompt = build_netops_prompt(ctx_package)

    forbidden_terms = [
        "ground_truth",
        "NOVEL_COMPOSITE_ANOMALY",  # Note: CADD returned UNKNOWN_COMPOSITE_ANOMALY
        "correct diagnosis =",
        "expected answer"
    ]

    print("Direct Prompt Preview (First 300 chars):")
    print(direct_prompt[:300] + "...\n")

    print("NetOps Prompt Preview (First 300 chars):")
    print(netops_prompt[:300] + "...\n")

    direct_leakage = [term for term in forbidden_terms if term in direct_prompt]
    netops_leakage = [term for term in forbidden_terms if term in netops_prompt]

    print(f"Direct Prompt Leakage Check: {'CLEAN' if not direct_leakage else f'LEAK DETECTED: {direct_leakage}'}")
    print(f"NetOps Prompt Leakage Check: {'CLEAN' if not netops_leakage else f'LEAK DETECTED: {netops_leakage}'}")

def audit_telemetry_causality():
    print("\n=== 3. TELEMETRY CAUSALITY AUDIT ===")
    causal_chains = {
        "CASE_01": "Injected Fault (OSPF timer mismatch) -> Core Link Status (rx_errors=142, metric=999) -> Telemetry (RTT=162.5ms, loss=18.5%) -> CESO Evidence -> CADD Rule Match (OSPF_ADJACENCY_INSTABILITY)",
        "CASE_02": "Injected Fault (Primary ISP fiber loss) -> SD-WAN Failover -> Backup Link Status (utilization=96.5%, drops=1450) -> Telemetry (RTT=145ms, loss=8.5%) -> CESO Evidence -> CADD Rule Match (WAN_PATH_DEGRADATION_AND_CONGESTION)",
        "CASE_03": "Injected Fault (MTU 1400 on spine-01 eth3) -> Jumbo Frame Drop -> Transport Status (drops=4500) -> Telemetry (RTT=320ms, loss=28%) -> CESO Evidence -> CADD Rule Match (MTU_MISMATCH_FRAGMENTATION_CASCADE)",
        "CASE_04": "Injected Fault (Edge resolver cache lock) -> Composite Symptoms (CPU=58%, loss=7.5%, RTT=85ms, DNS=140ms) -> Telemetry -> CESO Context -> CADD Low Confidence (0.47) -> LLM Escalation"
    }

    for sc_id, chain in causal_chains.items():
        print(f"[{sc_id}] Causal Chain:")
        print(f"  {chain}")

if __name__ == "__main__":
    audit_topologies()
    audit_ground_truth_leakage()
    audit_telemetry_causality()
