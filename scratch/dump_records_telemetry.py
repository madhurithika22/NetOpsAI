import json

rec1 = json.load(open("scratch/research_v2/phase2/runs/exp-phase2-5c538333.json"))
rec2 = json.load(open("scratch/research_v2/phase2/runs/exp-phase2-04052fa5.json"))

def dump_rec(rec, label):
    print(f"==================================================")
    print(f"REC: {label}")
    print(f"==================================================")
    print("baseline_snapshot:", json.dumps(rec.get("baseline_snapshot"), indent=2))
    print("fault_definition:", json.dumps(rec.get("fault_definition"), indent=2))
    print("fault_injection_record:", json.dumps(rec.get("fault_injection_record"), indent=2))
    print("diagnosis_record:", json.dumps(rec.get("diagnosis_record"), indent=2))

dump_rec(rec1, "exp-phase2-5c538333")
dump_rec(rec2, "exp-phase2-04052fa5")
