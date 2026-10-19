import os
import sys
import json
import hashlib
import subprocess
import glob

def find_files_containing(keyword, search_dirs):
    matches = []
    for d in search_dirs:
        if os.path.exists(d):
            for root, _, files in os.walk(d):
                for f in files:
                    if f.endswith((".py", ".md", ".json")):
                        filepath = os.path.join(root, f)
                        try:
                            content = open(filepath, "r", encoding="utf-8", errors="ignore").read()
                            if keyword.lower() in content.lower():
                                matches.append(filepath)
                        except Exception:
                            pass
    return matches

def main():
    print("=== READ-ONLY EXPERIMENTAL ARM COMPARABILITY AUDIT ===")
    
    # Git status before
    try:
        git_res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        print(f"Git status lines count before audit: {len(git_res.stdout.splitlines())}")
    except Exception as e:
        print("Git status error:", e)

    # Search for arm dispatch logic and evaluation runners
    search_dirs = ["backend/app", "scratch", "tests"]
    
    print("\n--- Searching for ARM_3, ARM_4, ARM_5 references ---")
    arm3_files = find_files_containing("ARM_3", search_dirs)
    arm4_files = find_files_containing("ARM_4", search_dirs)
    arm5_files = find_files_containing("ARM_5", search_dirs)
    
    print(f"Files referencing ARM_3 ({len(arm3_files)}): {arm3_files}")
    print(f"Files referencing ARM_4 ({len(arm4_files)}): {arm4_files}")
    print(f"Files referencing ARM_5 ({len(arm5_files)}): {arm5_files}")

    print("\n--- Searching for evaluation runner / dispatch code ---")
    runner_files = find_files_containing("runner", search_dirs)
    print(f"Files with 'runner' ({len(runner_files)}): {runner_files}")
    
    eval_files = find_files_containing("evaluat", search_dirs)
    print(f"Files with 'evaluat' ({len(eval_files)}): {eval_files}")

if __name__ == "__main__":
    main()
