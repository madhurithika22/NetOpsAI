import os
import sys
import json
import hashlib

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.models.ceso_models import NetworkState, InterfaceState, LinkLatency, RouteEntry
from app.cadd.engine import ExplainableRuleEngine

def md5_file(filepath):
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def run_audit():
    p2_path = "scratch/research_v2/phase2/runs/exp-phase2-5c538333.json"
    p2_orig_path = "scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json"

    print("==================================================")
    print("PHASE 2 INDEPENDENT RECORD VERIFICATION & FREEZE AUDIT")
    print("==================================================")

    print(f"\n1. FILE INTEGRITY & CHECKSUMS:")
    print(f"  {p2_path}: MD5 = {md5_file(p2_path)}")
    print(f"  {p2_orig_path}: MD5 = {md5_file(p2_orig_path)}")

    with open(p2_path, "r", encoding="utf-8") as f:
        rec = json.load(f)

    print(f"\n2. RECORD IDENTIFIERS & TIMESTAMPS:")
    print(f"  JSON Path 'experiment_id':                  {rec.get('experiment_id')}")
    print(f"  JSON Path 'run_id':                         {rec.get('run_id')}")
    print(f"  JSON Path 'timestamp':                      {rec.get('timestamp')}")
    print(f"  JSON Path 'testbed_version':                {rec.get('testbed_version')}")
    print(f"  JSON Path 'final_status':                   {rec.get('final_status')}")

    print(f"\n3. PERSISTED DIAGNOSIS RECORD (JSON Path 'diagnosis_record'):")
    diag = rec.get("diagnosis_record", {})
    print(f"  JSON Path 'diagnosis_record.diagnosis_id':      {diag.get('diagnosis_id')}")
    print(f"  JSON Path 'diagnosis_record.snapshot_id':       {diag.get('snapshot_id')}")
    print(f"  JSON Path 'diagnosis_record.timestamp':         {diag.get('timestamp')}")
    print(f"  JSON Path 'diagnosis_record.fault_type':         {diag.get('fault_type')}")
    print(f"  JSON Path 'diagnosis_record.confidence_score':   {diag.get('confidence_score')}")
    print(f"  JSON Path 'diagnosis_record.escalation_required':{diag.get('escalation_required')}")
    print(f"  JSON Path 'diagnosis_record.algorithm_version':  {diag.get('algorithm_version')}")
    print(f"  JSON Path 'diagnosis_record.algorithm_config':   {diag.get('algorithm_config')}")
    print(f"  JSON Path 'diagnosis_record.candidate_scores':   {json.dumps(diag.get('candidate_scores'), indent=4)}")

    print(f"\n4. PERSISTED EVALUATION GROUND-TRUTH (JSON Path 'evaluation_ground_truth'):")
    egt = rec.get("evaluation_ground_truth", {})
    print(f"  JSON Path 'evaluation_ground_truth.injected_fault_type': {egt.get('injected_fault_type')}")
    print(f"  JSON Path 'evaluation_ground_truth.injected_target':     {egt.get('injected_target')}")
    print(f"  JSON Path 'evaluation_ground_truth.diagnosis_correct':   {egt.get('diagnosis_correct')}")
    print("  -> Note: Ground-truth is joined AFTER operational prediction is saved to diagnosis_record.")

    print(f"\n5. RAW COMMAND HISTORY ANALYSIS (JSON Path 'raw_command_history'):")
    raw_history = rec.get("raw_command_history", [])
    print(f"  Total raw commands recorded: {len(raw_history)}")

    ping_events = []
    tc_events = []

    for idx, cmd in enumerate(raw_history):
        orig = cmd.get("original_command", [])
        eff = cmd.get("effective_command", [])
        ns = cmd.get("namespace")
        start = cmd.get("started_at")
        finish = cmd.get("finished_at")
        dur = cmd.get("duration_ms")
        ret = cmd.get("return_code")
        stdout = cmd.get("stdout", "")
        priv = cmd.get("privileged")

        if "ping" in orig:
            tx, rx, loss = 0, 0, 0.0
            for line in stdout.splitlines():
                if "packets transmitted" in line or "transmitted" in line:
                    parts = line.split(",")
                    tx = int(parts[0].split()[0])
                    rx = int(parts[1].split()[0])
                    calc_loss = round(((tx - rx) / tx) * 100.0, 4) if tx > 0 else 0.0
            ping_events.append({
                "idx": idx,
                "ns": ns,
                "orig": " ".join(orig),
                "tx": tx,
                "rx": rx,
                "lost": tx - rx,
                "calc_loss_pct": calc_loss,
                "ret": ret,
                "start": start,
                "finish": finish,
                "dur": dur,
                "stdout_summary": stdout.splitlines()[-2:] if stdout else []
            })
        elif "tc" in orig:
            tc_events.append({
                "idx": idx,
                "ns": ns,
                "orig": " ".join(orig),
                "ret": ret,
                "start": start,
                "finish": finish,
                "dur": dur,
                "stdout": stdout.strip()
            })

    print("\n  --- PING COMMANDS AUDIT ---")
    for p in ping_events:
        print(f"  Index {p['idx']:2d} | NS: {p['ns']:12s} | Cmd: {p['orig']:35s} | Tx={p['tx']:2d} Rx={p['rx']:2d} Lost={p['lost']:2d} CalcLoss={p['calc_loss_pct']:.4f}% | Code={p['ret']} | Dur={p['dur']}ms")
        print(f"           Start: {p['start']} | Finish: {p['finish']}")
        print(f"           Stdout summary: {' / '.join(p['stdout_summary'])}")

    print("\n  --- TRAFFIC CONTROL (tc) COMMANDS AUDIT ---")
    for t in tc_events:
        print(f"  Index {t['idx']:2d} | NS: {t['ns']:12s} | Cmd: {t['orig']:55s} | Code={t['ret']} | Dur={t['dur']}ms")
        if t['stdout']:
            print(f"           Stdout: {t['stdout'].replace(chr(10), ' | ')}")

    print(f"\n6. INDEPENDENT RECOMPUTATION OF DIAGNOSIS:")
    # Recreate the exact NetworkState supplied to CADE during degraded telemetry collection
    post_fault = rec.get("fault_injection_record", {}).get("post_fault_snapshot", {})
    post_ll = post_fault.get("link_latency", {})
    
    print(f"  Post-fault snapshot metrics: RTT={post_ll.get('rtt_avg_ms')} ms, Loss={post_ll.get('packet_loss_pct')} %")

    # Degraded telemetry state supplied to CADE in run_phase2_experiment.py
    # Note: RTT = 150.325 ms, Loss = 18.0 % (from 50-probe ping in step 6) or 26.67 % (from 30-probe ping in step 4)
    # Let's test both loss values through Engine:
    engine = ExplainableRuleEngine()

    for loss_val in [18.0, 26.6667]:
        test_state = NetworkState(
            snapshot_id="snap-audit-recompute",
            interfaces={"eth0": InterfaceState(name="eth0", is_up=True)},
            links=[LinkLatency(source_node="ha", target_node="hb", rtt_ms=150.325, packet_loss_pct=loss_val)],
            routes=[],
            anomalies_detected=True
        )
        rep, _ = engine.diagnose_state(test_state)
        print(f"\n  --- Recomputation for RTT=150.325ms, Loss={loss_val}% ---")
        print(f"  f_lat = clip((150.325 - 50)/50, 0, 1) = 1.0000")
        f_loss_calc = max(0.0, min(1.0, (loss_val - 10.0)/30.0))
        print(f"  f_loss = clip(({loss_val} - 10)/30, 0, 1) = {f_loss_calc:.4f}")
        s_calc = round(0.7 * 1.0 + 0.3 * f_loss_calc, 4)
        print(f"  S(HIGH_LATENCY_CONGESTION) = 0.7*1.0 + 0.3*{f_loss_calc:.4f} = {s_calc:.4f}")
        print(f"  Engine Candidate Scores: {rep.candidate_scores}")
        print(f"  Engine Confidence Score: {rep.confidence_score}")
        print(f"  Engine Escalation Flag:   {rep.escalation_required}")

if __name__ == "__main__":
    run_audit()
