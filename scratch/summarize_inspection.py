import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/dataset_inspection.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total dataset size: {data['dataset_size_gb']} GB ({data['dataset_size_mb']} MB)")
print(f"Total root files: {data['file_count']}")

print("\n=== EXCEL DOCUMENT SUMMARIES ===")
for doc, sheets in data['excel_docs'].items():
    print(f"\n-- {doc} --")
    for sname, sinfo in sheets.items():
        if isinstance(sinfo, dict) and 'total_rows' in sinfo:
            print(f"  Sheet: {sname} | Rows: {sinfo['total_rows']}")
            print(f"    Header: {sinfo['header']}")
            for i, r in enumerate(sinfo['sample_rows'][:3]):
                print(f"    Sample row {i+1}: {r}")

print("\n=== ZIP ARCHIVES SUMMARY ===")
for zname, zinfo in data['zip_archives'].items():
    print(f"{zname}: {zinfo['compressed_mb']} MB compressed ({zinfo.get('file_count', 0)} files)")
    print(f"  Sample files: {zinfo.get('sample_files', [])[:5]}")
