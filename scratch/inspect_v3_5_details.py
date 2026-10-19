import os
import sys
import json
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')

dataset_dir = r"data/external/aiops_challenge_2020"
v3_5_dir = os.path.join(dataset_dir, "data_release_v3.5")

def get_xlsx_all_rows(xlsx_path):
    sheets_data = {}
    with zipfile.ZipFile(xlsx_path, 'r') as z:
        wb_xml = z.read('xl/workbook.xml')
        wb_root = ET.fromstring(wb_xml)
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            ss_xml = z.read('xl/sharedStrings.xml')
            ss_root = ET.fromstring(ss_xml)
            for si in ss_root.findall('.//main:si', ns):
                # Concatenate all text inside si
                texts = [t.text for t in si.findall('.//main:t', ns) if t.text]
                shared_strings.append(''.join(texts))
        
        sheet_elements = wb_root.findall('.//main:sheet', ns)
        for idx, sheet_el in enumerate(sheet_elements):
            sname = sheet_el.attrib.get('name', f'Sheet{idx+1}')
            sheet_file = f'xl/worksheets/sheet{idx+1}.xml'
            if sheet_file not in z.namelist():
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
            
            sheets_data[sname] = rows_data
    return sheets_data

import zipfile
for ef in os.listdir(v3_5_dir):
    if ef.endswith(".xlsx") and not ef.startswith("~$"):
        print(f"================ FILE: {ef} ================")
        full_p = os.path.join(v3_5_dir, ef)
        sdata = get_xlsx_all_rows(full_p)
        for sname, rows in sdata.items():
            print(f"--- Sheet: {sname} (Total rows: {len(rows)}) ---")
            for r in rows[:15]:
                print(r)
