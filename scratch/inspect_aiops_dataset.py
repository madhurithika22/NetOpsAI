import os
import sys
import glob
import zipfile
import json
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

dataset_dir = r"data/external/aiops_challenge_2020"
output_file = r"scratch/dataset_inspection.json"
os.makedirs("scratch", exist_ok=True)

def parse_xlsx_sheets(xlsx_path):
    """Simple parser for xlsx files using zipfile and ElementTree."""
    sheets_data = {}
    try:
        with zipfile.ZipFile(xlsx_path, 'r') as z:
            # Read workbook.xml to get sheet names
            wb_xml = z.read('xl/workbook.xml')
            wb_root = ET.fromstring(wb_xml)
            ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            
            # Read shared strings
            shared_strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                ss_xml = z.read('xl/sharedStrings.xml')
                ss_root = ET.fromstring(ss_xml)
                for si in ss_root.findall('.//main:si', ns):
                    t = si.find('.//main:t', ns)
                    shared_strings.append(t.text if t is not None else '')
            
            sheet_elements = wb_root.findall('.//main:sheet', ns)
            for idx, sheet_el in enumerate(sheet_elements):
                sname = sheet_el.attrib.get('name', f'Sheet{idx+1}')
                r_id = sheet_el.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id', f'rId{idx+1}')
                
                sheet_file = f'xl/worksheets/sheet{idx+1}.xml'
                if sheet_file not in z.namelist():
                    # Fallback try by sheetId or index
                    sheet_files = [f for f in z.namelist() if f.startswith('xl/worksheets/sheet')]
                    if idx < len(sheet_files):
                        sheet_file = sheet_files[idx]
                    else:
                        continue

                sheet_xml = z.read(sheet_file)
                s_root = ET.fromstring(sheet_xml)
                
                rows_data = []
                for row in s_root.findall('.//main:row', ns):
                    r_vals = []
                    for c in row.findall('.//main:c', ns):
                        t_type = c.attrib.get('t')
                        v_el = c.find('main:v', ns)
                        val = v_el.text if v_el is not None else ''
                        if t_type == 's' and val.isdigit() and int(val) < len(shared_strings):
                            val = shared_strings[int(val)]
                        r_vals.append(val)
                    if r_vals:
                        rows_data.append(r_vals)
                
                sheets_data[sname] = {
                    "total_rows": len(rows_data),
                    "header": rows_data[0] if rows_data else [],
                    "sample_rows": rows_data[1:10] if len(rows_data) > 1 else []
                }
    except Exception as e:
        sheets_data["error"] = str(e)
    return sheets_data

report = {}

# 1. Size & Inventory
total_bytes = 0
files_list = []
for root, dirs, files in os.walk(dataset_dir):
    for f in files:
        fpath = os.path.join(root, f)
        relpath = os.path.relpath(fpath, dataset_dir).replace("\\", "/")
        size = os.path.getsize(fpath)
        total_bytes += size
        files_list.append({
            "path": relpath,
            "size_bytes": size,
            "size_mb": round(size / (1024 * 1024), 2)
        })

report["dataset_size_bytes"] = total_bytes
report["dataset_size_mb"] = round(total_bytes / (1024 * 1024), 2)
report["dataset_size_gb"] = round(total_bytes / (1024 * 1024 * 1024), 2)
report["file_count"] = len(files_list)
report["files"] = files_list

# 2. XLSX Files Parsing
v3_5_dir = os.path.join(dataset_dir, "data_release_v3.5")
excel_files = glob.glob(os.path.join(v3_5_dir, "*.xlsx"))
report["excel_docs"] = {}
for ef in sorted(excel_files):
    fname = os.path.basename(ef)
    if fname.startswith("~$"):
        continue
    report["excel_docs"][fname] = parse_xlsx_sheets(ef)

# 3. Zip Archives Contents
report["zip_archives"] = {}
zip_files = sorted(glob.glob(os.path.join(dataset_dir, "*.zip")))
for zf_path in zip_files:
    zname = os.path.basename(zf_path)
    try:
        with zipfile.ZipFile(zf_path, 'r') as z:
            names = z.namelist()
            report["zip_archives"][zname] = {
                "file_count": len(names),
                "compressed_mb": round(os.path.getsize(zf_path) / (1024 * 1024), 2),
                "uncompressed_mb": round(sum(i.file_size for i in z.infolist()) / (1024 * 1024), 2),
                "sample_files": names[:15]
            }
    except Exception as e:
        report["zip_archives"][zname] = {"error": str(e)}

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"Inspection summary written to {output_file}")
