import json

rec1 = json.load(open("scratch/research_v2/phase2/runs/exp-phase2-5c538333.json"))
rec2 = json.load(open("scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json"))

print("=== REC 1 (exp-phase2-5c538333) ===")
print("Top-level keys:", list(rec1.keys()))
print("diagnosis_record:", rec1.get("diagnosis_record"))
print("baseline_snapshot keys:", list(rec1.get("baseline_snapshot", {}).keys()))
print("baseline_snapshot links:", rec1.get("baseline_snapshot", {}).get("links"))
print("baseline_snapshot interfaces:", list(rec1.get("baseline_snapshot", {}).get("interfaces", {}).keys()))

print("\n=== REC 2 (exp-phase2-04052fa5) ===")
print("Top-level keys:", list(rec2.keys()))
print("diagnosis_record:", rec2.get("diagnosis_record"))
print("baseline_snapshot keys:", list(rec2.get("baseline_snapshot", {}).keys()))
print("baseline_snapshot links:", rec2.get("baseline_snapshot", {}).get("links"))
print("baseline_snapshot interfaces:", list(rec2.get("baseline_snapshot", {}).get("interfaces", {}).keys()))
