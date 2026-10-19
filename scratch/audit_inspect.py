import os
import sys
import json

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.cadd.engine import ExplainableRuleEngine

with open("scratch/research_v2/phase2/runs/exp-phase2-5c538333.json", "r", encoding="utf-8") as f:
    rec = json.load(f)

print("==================================================")
print("RECORD: exp-phase2-5c538333.json")
print("==================================================")

diag = rec.get("diagnosis_record", {})
candidate_scores = diag.get("candidate_scores", {})

print("\n1. CANDIDATE SCORES FROM RECORD:")
for k, v in candidate_scores.items():
    print(f"  {k}: {v}")

# Sort candidates by numeric score descending, then tie-breaking priority
sorted_c = sorted(
    candidate_scores.keys(),
    key=lambda c: (candidate_scores[c], -ExplainableRuleEngine.TIE_BREAKING_PRIORITY.index(c)),
    reverse=True
)

top_1 = sorted_c[0]
score_1 = candidate_scores[top_1]

top_2 = sorted_c[1]
score_2 = candidate_scores[top_2]

print("\n2. INDEPENDENT RANKING & TOP-2 EXTRACTION:")
print(f"  Top Candidate:        {top_1} = {score_1}")
print(f"  Second Candidate:     {top_2} = {score_2}")

recomputed_conf = round(score_1 * (1.0 - 0.5 * score_2), 4)
stored_conf = diag.get("confidence_score")
print(f"  Stored Confidence:    {stored_conf}")
print(f"  Recomputed Confidence:{recomputed_conf}")
print(f"  Match:                {stored_conf == recomputed_conf}")

escalation_required = (recomputed_conf < ExplainableRuleEngine.CONFIDENCE_ESCALATION_THRESHOLD) or (top_1 == "UNKNOWN_COMPOSITE_ANOMALY")
stored_esc = diag.get("escalation_required")
print(f"  Stored Escalation:    {stored_esc}")
print(f"  Recomputed Escalation:{escalation_required}")
print(f"  Match:                {stored_esc == escalation_required}")

print("\n3. INSPECTING ALL RAW COMMANDS IN exp-phase2-5c538333.json:")
raw_cmds = rec.get("raw_command_history", [])
print(f"Total commands in raw_command_history: {len(raw_cmds)}")

ping_cmds = []
tc_cmds = []
for i, cmd in enumerate(raw_cmds):
    orig = cmd.get("original_command", [])
    cmd_str = " ".join(orig)
    if "ping" in orig:
        ping_cmds.append((i, cmd))
    elif "tc" in orig:
        tc_cmds.append((i, cmd))

print(f"\nPing commands found ({len(ping_cmds)}):")
for idx, cmd in ping_cmds:
    print(f"\n--- Ping Cmd Index {idx} ---")
    print("Namespace:     ", cmd.get("namespace"))
    print("Effective Cmd: ", " ".join(cmd.get("effective_command", [])))
    print("Started At:    ", cmd.get("started_at"))
    print("Finished At:   ", cmd.get("finished_at"))
    print("Duration ms:   ", cmd.get("duration_ms"))
    print("Return Code:   ", cmd.get("return_code"))
    print("Stdout:")
    print(cmd.get("stdout", "").strip())

print(f"\nTraffic Control (tc) commands found ({len(tc_cmds)}):")
for idx, cmd in tc_cmds:
    print(f"\n--- tc Cmd Index {idx} ---")
    print("Namespace:     ", cmd.get("namespace"))
    print("Effective Cmd: ", " ".join(cmd.get("effective_command", [])))
    print("Return Code:   ", cmd.get("return_code"))
    print("Stdout:")
    print(cmd.get("stdout", "").strip())
