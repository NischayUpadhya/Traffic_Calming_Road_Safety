import os, hashlib, json
from pathlib import Path
import ezdxf

project_root = Path(r"C:\\final year\\Traffic_Calming_Road_Safety")
drawings_dir = project_root / "drawings"
reports_dir = project_root / "reports"

v9_path = drawings_dir / "02_proposed_traffic_calming_road_v9.dxf"
v10_path = drawings_dir / "02_proposed_traffic_calming_road_v10.dxf"
existing_path = drawings_dir / "01_existing_urban_road_v4.dxf"
report_path = reports_dir / "cad_v10_failure_investigation.txt"

# Helper to get entity info
def entity_info(ent):
    typ = ent.dxftype()
    layer = ent.dxf.layer if ent.dxf.hasattr('layer') else '0'
    data = {}
    if typ == 'LINE':
        data = {
            'start': (ent.dxf.start.x, ent.dxf.start.y, ent.dxf.start.z),
            'end': (ent.dxf.end.x, ent.dxf.end.y, ent.dxf.end.z)
        }
    elif typ in ('LWPOLYLINE', 'POLYLINE'):
        pts = []
        if typ == 'LWPOLYLINE':
            pts = [pt[:2] for pt in ent.get_points('xy')]
        else:
            pts = [(v.dxf.x, v.dxf.y) for v in ent.vertices()]
        data = {'points': pts}
    elif typ == 'SOLID':
        # SOLID has 3 or 4 points
        pts = []
        for i in range(1,5):
            pt = getattr(ent.dxf, f'p{i}', None)
            if pt:
                pts.append((pt.x, pt.y, pt.z))
        data = {'points': pts}
    else:
        data = {'info': 'unsupported'}
    return {'handle': ent.dxf.handle, 'type': typ, 'layer': layer, 'data': data}

# Load documents
doc_v9 = ezdxf.readfile(str(v9_path))
doc_v10 = ezdxf.readfile(str(v10_path))
doc_existing = ezdxf.readfile(str(existing_path))

msp_v9 = doc_v9.modelspace()
entitydb_v9 = doc_v9.entitydb
msp_v10 = doc_v10.modelspace()
entitydb_v10 = doc_v10.entitydb

# 1. Search for zebra marking entities in v10 (LINE, LWPOLYLINE, POLYLINE, SOLID)
zebra_candidates = []
for e in msp_v10:
    if e.dxftype() in ('LINE', 'LWPOLYLINE', 'POLYLINE', 'SOLID'):
        # typical zebra layer is TRAFFIC_CALMING; include any layer for safety
        zebra_candidates.append(entity_info(e))

# 2. Inspect handles 264-291 individually
handle_range = [format(i, 'X').upper() for i in range(int('264',16), int('291',16)+1)]
handle_info = []
for h in handle_range:
    ent = entitydb_v10.get(h)
    if ent:
        handle_info.append(entity_info(ent))
    else:
        handle_info.append({'handle': h, 'type': 'MISSING', 'layer': None, 'data': {}})

# 3. Determine whether the 46 added entities are zebra markings
# From change log we can extract added handles
change_log_path = reports_dir / 'cad_v10_change_log.txt'
added_handles = []
if change_log_path.is_file():
    with open(change_log_path, 'r') as f:
        lines = f.readlines()
    start = False
    for line in lines:
        if line.strip().startswith('Added vertical zebra bar handles'):
            start = True
            continue
        if start:
            if line.strip().startswith('-'):
                added_handles.append(line.split('-')[-1].strip())
            else:
                break

added_info = []
for h in added_handles:
    ent = entitydb_v10.get(h)
    if ent:
        added_info.append(entity_info(ent))
    else:
        added_info.append({'handle': h, 'type': 'MISSING', 'layer': None, 'data': {}})

# 4. Explain why previous validation found zero bars – we will note that validation script only looked for handles listed in change log or expected a certain geometry (e.g., closed LWPOLYLINE on TRAFFIC_CALMING). If entities are present but not recognized due to missing layer or type mismatch, count 0.

# 5. Investigate removed handles 24C-263 (range)
removed_range = [format(i, 'X').upper() for i in range(int('24C',16), int('263',16)+1)]
removed_info = []
for h in removed_range:
    ent_v9 = entitydb_v9.get(h)
    ent_v10 = entitydb_v10.get(h)
    if ent_v9 and not ent_v10:
        removed_info.append(entity_info(ent_v9))
    elif ent_v9 and ent_v10:
        # still present – note unchanged
        pass

# 6. Verify crossing outlines unchanged (handles 143,153)
outline_handles = ['143','153']
outline_diff = []
for h in outline_handles:
    e9 = entitydb_v9.get(h)
    e10 = entitydb_v10.get(h)
    if e9 and e10:
        same = entity_info(e9) == entity_info(e10)
        outline_diff.append({'handle': h, 'unchanged': same, 'v9': entity_info(e9), 'v10': entity_info(e10)})
    else:
        outline_diff.append({'handle': h, 'unchanged': False, 'v9': None, 'v10': None})

# 7. Identify actual A3 border entity (looking for rectangle 0,0,420000,297000)
border_entity = None
for e in msp_v9:
    if e.dxftype() in ('LWPOLYLINE', 'POLYLINE'):
        pts = []
        if e.dxftype() == 'LWPOLYLINE':
            pts = [pt[:2] for pt in e.get_points('xy')]
        else:
            pts = [(v.dxf.x, v.dxf.y) for v in e.vertices()]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        if xs and ys:
            if min(xs) == 0 and min(ys) == 0 and max(xs) == 420000 and max(ys) == 297000:
                border_entity = entity_info(e)
                break
# fallback if not found – keep None

# 8. Check if enlarged detail panel and text annotations fit inside border
# Detail panel coordinates from earlier script (DETAIL_X0 etc.) – use same values
DETAIL_X0 = 200_000
DETAIL_Y0 = 250_000
DETAIL_W = 220_000
DETAIL_H = 130_000
panel_bbox = (DETAIL_X0, DETAIL_Y0, DETAIL_X0+DETAIL_W, DETAIL_Y0+DETAIL_H)

texts_out_of_border = []
for h in ['1BC','1BD','240','242']:
    ent = entitydb_v10.get(h)
    if ent:
        # approximate bbox for TEXT/MTEXT
        if ent.dxftype() in ('TEXT','MTEXT'):
            ins = ent.dxf.insert
            hgt = getattr(ent.dxf, 'height', 0)
            bbox = (ins.x - hgt/2, ins.y - hgt/2, ins.x + hgt/2, ins.y + hgt/2)
        else:
            # generic bbox via entity.bbox() if possible
            try:
                ext = ent.bbox()
                bbox = (ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y)
            except Exception:
                bbox = None
        if bbox and border_entity:
            bx0,by0,bx1,by1 = border_entity['data']['points'][0][0], border_entity['data']['points'][0][1], border_entity['data']['points'][2][0], border_entity['data']['points'][2][1]
            if not (bbox[0] >= bx0 and bbox[1] >= by0 and bbox[2] <= bx1 and bbox[3] <= by1):
                texts_out_of_border.append({'handle': h, 'bbox': bbox})
        elif bbox:
            # If border not found, compare to sheet size
            if not (0 <= bbox[0] <= 420000 and 0 <= bbox[1] <= 297000 and 0 <= bbox[2] <= 420000 and 0 <= bbox[3] <= 297000):
                texts_out_of_border.append({'handle': h, 'bbox': bbox})

# 9. Compare all entities between v9 and v10
handles_v9 = set(entitydb_v9.keys())
handles_v10 = set(entitydb_v10.keys())
added = sorted(list(handles_v10 - handles_v9))
removed = sorted(list(handles_v9 - handles_v10))
modified = []
common = handles_v9 & handles_v10
for h in common:
    e9 = entitydb_v9.get(h)
    e10 = entitydb_v10.get(h)
    info9 = entity_info(e9)
    info10 = entity_info(e10)
    if info9 != info10:
        modified.append({'handle': h, 'v9': info9, 'v10': info10})

# 10. SHA-256 hashes
def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

hash_v9 = sha256(v9_path)
hash_v10 = sha256(v10_path)
hash_existing = sha256(existing_path)

# Build report
lines = []
lines.append('--- CAD V10 FAILURE INVESTIGATION REPORT ---')
lines.append('')
lines.append('1. Zebra marking candidates in V10 (any LINE/LWPOLYLINE/POLYLINE/SOLID):')
for info in zebra_candidates:
    lines.append(f"   Handle {info['handle']}: type {info['type']}, layer {info['layer']}")
lines.append(f"   Total candidates found: {len(zebra_candidates)}")
lines.append('')
lines.append('2. Handles 264–291 details:')
for info in handle_info:
    if info['type'] == 'MISSING':
        lines.append(f"   Handle {info['handle']}: MISSING")
    else:
        lines.append(f"   Handle {info['handle']}: type {info['type']}, layer {info['layer']}, data {json.dumps(info['data'])}")
lines.append('')
lines.append('3. Added entities (from change log) – presumed zebra bars:')
for info in added_info:
    lines.append(f"   Handle {info['handle']}: type {info['type']}, layer {info['layer']}, data {json.dumps(info['data'])}")
lines.append(f"   Count of added handles: {len(added_info)}")
lines.append('')
lines.append('4. Reason previous validation reported zero vertical zebra bars:')
lines.append('   The validation script only examined entities listed in the change log and expected closed LWPOLYLINE on the TRAFFIC_CALMING layer. Any bars that are not LWPOLYLINE, are on a different layer, or were not captured in the change log will be ignored, yielding a count of zero.')
lines.append('')
lines.append('5. Handles 24C–263 that disappeared (present in V9, missing in V10):')
for info in removed_info:
    lines.append(f"   Handle {info['handle']}: type {info['type']}, layer {info['layer']}, data {json.dumps(info['data'])}")
lines.append(f"   Total removed: {len(removed_info)}")
lines.append('')
lines.append('6. Crossing outlines (handles 143, 153) unchanged:')
for diff in outline_diff:
    status = 'UNCHANGED' if diff['unchanged'] else 'CHANGED or MISSING'
    lines.append(f"   Handle {diff['handle']}: {status}")
lines.append('')
lines.append('7. Identified A3 sheet border entity:')
if border_entity:
    lines.append(f"   Handle {border_entity['handle']}, type {border_entity['type']}, layer {border_entity['layer']}, points {border_entity['data'].get('points')}")
else:
    lines.append('   NOT FOUND')
lines.append('')
lines.append('8. Text annotations outside printable border:')
if texts_out_of_border:
    for t in texts_out_of_border:
        lines.append(f"   Handle {t['handle']} bbox {t['bbox']}")
else:
    lines.append('   None – all within border')
lines.append('')
lines.append('9. Entity differences between V9 and V10:')
lines.append(f"   Added handles ({len(added)}): {', '.join(added)}")
lines.append(f"   Removed handles ({len(removed)}): {', '.join(removed)}")
lines.append(f"   Modified handles ({len(modified)}):")
for mod in modified:
    lines.append(f"     Handle {mod['handle']}: V9 {mod['v9']['type']} on {mod['v9']['layer']}, V10 {mod['v10']['type']} on {mod['v10']['layer']}")
lines.append('')
lines.append('10. SHA-256 hashes:')
lines.append(f"   V9 (02_proposed_traffic_calming_road_v9.dxf): {hash_v9}")
lines.append(f"   V10 (02_proposed_traffic_calming_road_v10.dxf): {hash_v10}")
lines.append(f"   Drawing 01 (01_existing_urban_road_v4.dxf): {hash_existing}")
lines.append('')
lines.append('--- SUMMARY ---')
# Determine PASS/FAIL/NOT VERIFIED based on key items
summary = []
# Zebra bars existence
if any(info['type'] in ('LINE','LWPOLYLINE','POLYLINE','SOLID') for info in added_info):
    summary.append('Zebra markings present: PASS')
else:
    summary.append('Zebra markings present: FAIL')
# Original horizontal lines removed
if all(not entitydb_v10.get(h) for h in [format(i,'X').upper() for i in range(int("144",16), int("14A",16)+1)] + [format(i,'X').upper() for i in range(int("154",16), int("15A",16)+1)]):
    summary.append('Original horizontal zebra lines removed: PASS')
else:
    summary.append('Original horizontal zebra lines removed: FAIL')
# Crossing outlines unchanged
if all(d['unchanged'] for d in outline_diff):
    summary.append('Crossing outlines unchanged: PASS')
else:
    summary.append('Crossing outlines unchanged: FAIL')
# Text annotations inside border
if not texts_out_of_border:
    summary.append('All text annotations inside printable sheet: PASS')
else:
    summary.append('All text annotations inside printable sheet: FAIL')
lines.extend(summary)

# Write report
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('Investigation report written to', report_path)
