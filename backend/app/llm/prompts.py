import json
from typing import Dict, Any
from app.llm.models import LLMContextPackage

SYSTEM_PROMPT = """You are an expert Network AIOps Reasoning and Incident Remediation Assistant.
Your task is to analyze network state evidence, identify root cause, evaluate candidate remediation safety, and recommend precise actions.
Always provide your answer in valid JSON format matching this schema:
{
  "diagnosis": "SHORT_DIAGNOSIS_LABEL",
  "reasoning_summary": "Detailed technical explanation of root cause and causal chain.",
  "evidence": ["evidence item 1", "evidence item 2"],
  "confidence": 0.85,
  "recommended_action": {
    "action_id": "act-recommended",
    "command_type": "COMMAND_NAME",
    "target_device": "device_id",
    "parameters": {"param1": "val1"}
  },
  "alternatives": ["alternative action 1"],
  "uncertainty": "Description of any unknown variables or assumptions"
}
Do NOT wrap JSON in extra markdown text if possible. Ensure valid JSON output."""

DIRECT_RAW_LOGS_PROMPT_TEMPLATE = """Analyze the following RAW network telemetry and uncompressed log output to diagnose the incident:

[RAW TELEMETRY & METRICS]
{raw_telemetry_json}

[RAW NETWORK SYSLOGS]
{raw_logs}

[TOPOLOGY EVENTS]
{topology_events}

Perform root cause analysis and output your structured JSON diagnosis."""

NETOPS_CONTEXT_PACKAGE_PROMPT_TEMPLATE = """Analyze the following NetOps Context Package distilled by CESO, CADD, and MSVS:

[SCENARIO & INCIDENT]
Incident ID: {incident_id}
Scenario: {scenario_id}
Timestamp: {timestamp}

[TOPOLOGY SUMMARY]
Nodes Count: {topology_nodes_count}
Links Count: {topology_links_count}
Affected Nodes: {affected_nodes}
Affected Links: {affected_links}

[OBSERVED OPERATIONAL TELEMETRY]
{relevant_telemetry}

[DISTILLED CESO FINDINGS]
{ceso_findings}

[CORRELATED ANOMALIES]
{correlated_anomalies}

[CADD PRELIMINARY DIAGNOSIS]
Preliminary Diagnosis: {cadd_diagnosis}
Confidence: {diagnosis_confidence}
Candidate Causes: {candidate_causes}

[MSVS SAFETY CONSTRAINTS & PERMITTED ACTIONS]
{msvs_safety_constraints}

[CANDIDATE REMEDIATION ACTIONS]
{candidate_remediation_actions}

[VERIFICATION REQUIREMENTS]
{verification_requirements}

Provide your refined diagnosis, reasoning, and safest recommended action in structured JSON."""

POST_ACTION_FEEDBACK_PROMPT_TEMPLATE = """Assess the following post-remediation verification feedback:

Action Executed: {action_id}
Result: {result}
Verification Passed: {verification_passed}

[METRIC CHANGES]
Pre-Action Metrics: {pre_action_metrics}
Post-Action Metrics: {post_action_metrics}
Deltas: {metric_deltas}

[AFFECTED SERVICES & OBSERVED SIDE EFFECTS]
Affected Services: {affected_services}
Observed Side Effects: {observed_side_effects}

Provide your post-action assessment in valid JSON:
{{
  "diagnosis_supported": true,
  "remediation_effective": true,
  "additional_action_required": false,
  "observation_recommended": true,
  "assessment_summary": "Detailed technical assessment of post-action stability."
}}"""

def build_direct_prompt(raw_telemetry: Dict[str, Any], raw_logs: list, topology_events: list) -> str:
    return DIRECT_RAW_LOGS_PROMPT_TEMPLATE.format(
        raw_telemetry_json=json.dumps(raw_telemetry, indent=2),
        raw_logs="\n".join(raw_logs) if raw_logs else "No syslog messages recorded.",
        topology_events="\n".join(topology_events) if topology_events else "No topology state change events."
    )

def format_telemetry_summary(telemetry: Dict[str, Any]) -> str:
    """
    Formats the sanitized telemetry dictionary into a clean, concise representation
    suitable for LLM reasoning while preserving token efficiency.
    """
    if not telemetry:
        return "No additional telemetry recorded."

    lines = []
    if "interfaces" in telemetry and telemetry["interfaces"]:
        lines.append("Interfaces:")
        for name, if_data in telemetry["interfaces"].items():
            lines.append(
                f"  - {name}: up={if_data.get('is_up')}, mtu={if_data.get('mtu')}, "
                f"util={if_data.get('utilization_pct')}%, rx_err={if_data.get('rx_errors')}, "
                f"tx_err={if_data.get('tx_errors')}, rx_drop={if_data.get('rx_drops')}, "
                f"tx_drop={if_data.get('tx_drops')}"
            )
    if "links" in telemetry and telemetry["links"]:
        lines.append("Links:")
        for l in telemetry["links"]:
            lines.append(
                f"  - {l.get('source')} <-> {l.get('target')}: status={l.get('status')}, "
                f"rtt={l.get('rtt_ms')}ms, loss={l.get('packet_loss_pct')}%"
            )
    if "routes" in telemetry and telemetry["routes"]:
        lines.append("Routes:")
        for r in telemetry["routes"]:
            lines.append(
                f"  - dst={r.get('destination')}, gw={r.get('gateway')}, "
                f"iface={r.get('interface')}, metric={r.get('metric')}"
            )
    if "nodes" in telemetry and telemetry["nodes"]:
        lines.append("Nodes:")
        for n_id, n_data in telemetry["nodes"].items():
            lines.append(
                f"  - {n_id}: cpu={n_data.get('cpu_utilization_pct')}%, "
                f"mem={n_data.get('memory_utilization_pct')}%"
            )
    if "anomalies_detected" in telemetry:
        lines.append(f"Anomalies Detected: {telemetry['anomalies_detected']}")

    return "\n".join(lines) if lines else json.dumps(telemetry)


def format_verification_summary(verif: Dict[str, Any]) -> str:
    if not verif:
        return "Standard verification criteria apply."
    return ", ".join(f"{k}: {v}" for k, v in verif.items())


def build_netops_prompt(ctx: LLMContextPackage) -> str:
    telemetry_str = format_telemetry_summary(ctx.relevant_telemetry)
    verification_str = format_verification_summary(ctx.verification_requirements)
    remediation_str = json.dumps(ctx.candidate_remediation_actions, indent=2) if ctx.candidate_remediation_actions else "None (Escalation requires independent safe action recommendation from permitted command types)"

    return NETOPS_CONTEXT_PACKAGE_PROMPT_TEMPLATE.format(
        incident_id=ctx.incident_id,
        scenario_id=ctx.scenario_id,
        timestamp=ctx.timestamp,
        topology_nodes_count=ctx.topology_summary.get("node_count", 0),
        topology_links_count=ctx.topology_summary.get("link_count", 0),
        affected_nodes=", ".join(ctx.affected_nodes) if ctx.affected_nodes else "None",
        affected_links=", ".join(ctx.affected_links) if ctx.affected_links else "None",
        relevant_telemetry=telemetry_str,
        ceso_findings="\n".join(f"- {f}" for f in ctx.ceso_findings) if ctx.ceso_findings else "None",
        correlated_anomalies="\n".join(f"- {a}" for a in ctx.correlated_anomalies) if ctx.correlated_anomalies else "None",
        cadd_diagnosis=ctx.cadd_diagnosis,
        diagnosis_confidence=ctx.diagnosis_confidence,
        candidate_causes=", ".join(ctx.candidate_causes) if ctx.candidate_causes else "None",
        msvs_safety_constraints="\n".join(f"- {c}" for c in ctx.msvs_safety_constraints) if ctx.msvs_safety_constraints else "None",
        candidate_remediation_actions=remediation_str,
        verification_requirements=verification_str
    )

def build_feedback_prompt(action_id: str, result: str, verification_passed: bool, pre_metrics: dict, post_metrics: dict, deltas: dict, services: list, side_effects: list) -> str:
    return POST_ACTION_FEEDBACK_PROMPT_TEMPLATE.format(
        action_id=action_id,
        result=result,
        verification_passed=verification_passed,
        pre_action_metrics=json.dumps(pre_metrics),
        post_action_metrics=json.dumps(post_metrics),
        metric_deltas=json.dumps(deltas),
        affected_services=", ".join(services),
        observed_side_effects=", ".join(side_effects) if side_effects else "None"
    )
