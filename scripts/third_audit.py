import ezdxf, json, os, re
from pathlib import Path

project_root = Path(r"C:\\final year\\Traffic_Calming_Road_Safety")

v10_path = project_root / "drawings" / "02_proposed_traffic_calming_road_v10.dxf"
report_path = project_root / "reports" / "cad_v11_layout_correction_third_audit.txt"

# Load DXF
if not v10_path.is_file():
    raise FileNotFoundError(f"v10 DXF not found at {v10_path}")

doc = ezdxf.readfile(str(v10_path))
entitydb = doc.entitydb
msp = doc.modelspace()

# Helper to extract points and bbox
def get_entity_points(ent):
    typ = ent.dxftype()
    if typ == 'LINE':
        return [(ent.dxf.start.x, ent.dxf.start.y), (ent.dxf.end.x, ent.dxf.end.y)]
    if typ in ('LWPOLYLINE', 'POLYLINE'):
        if typ == 'LWPOLYLINE':
            return [pt[:2] for pt in ent.get_points('xy')]
        else:
            return [(v.dxf.x, v.dxf.y) for v in ent.vertices()]
    if typ in ('TEXT', 'MTEXT'):
        ins = ent.dxf.insert
        return [(ins.x, ins.y)]
    if typ == 'INSERT':
        ins = ent.dxf.insert
        return [(ins.x, ins.y)]
    return []

def bbox_from_pts(pts):
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))

# 1. Verify specific handles
handles_of_interest = ['1BB', '1BE', '1BF', '1C0', '1C2', '243', '245']
handle_info = {}
for h in handles_of_interest:
    ent = entitydb.get(h)
    if not ent:
        handle_info[h] = None
        continue
    typ = ent.dxftype()
    layer = ent.dxf.layer if ent.dxf.hasattr('layer') else None
    pts = get_entity_points(ent)
    bbox = bbox_from_pts(pts)
    handle_info[h] = {'type': typ, 'layer': layer, 'points': pts, 'bbox': bbox}

# 2. Load earlier audit reports to compare (if they exist)
prev_reports = [
    project_root / "reports" / "cad_v10_final_layout_investigation.txt",
    project_root / "reports" / "cad_v11_layout_correction_plan.txt",
    project_root / "reports" / "cad_v11_layout_correction_revised_plan.txt"
]
prev_data = {}
for rp in prev_reports:
    if not rp.is_file():
        continue
    text = rp.read_text(encoding='utf-8')
    # simple regex to capture lines with handle info
    for line in text.splitlines():
        m = re.search(r"Handle\s+(\w+):.*type\s+(\w+).*layer\s+(\w+).*bbox\s*\(([^)]+)\)", line)
        if m:
            h, t, l, bbox_str = m.groups()
            vals = [float(v.strip()) for v in bbox_str.split(',')]
            prev_data[h] = {'type': t, 'layer': l, 'bbox': tuple(vals)}

# 3. Identify complete enlarged-detail group
# Start with detail outline (1C2) bbox
outline_ent = entitydb.get('1C2')
outline_bbox = bbox_from_pts(get_entity_points(outline_ent)) if outline_ent else None
if not outline_bbox:
    raise ValueError('Detail outline handle 1C2 not found or has no geometry')
# Expand outline bbox generously to capture related objects (e.g., 5000 mm each side)
expand = 5000
expanded_bbox = (outline_bbox[0]-expand, outline_bbox[1]-expand, outline_bbox[2]+expand, outline_bbox[3]+expand)

def point_in_bbox(pt, bbox):
    x,y = pt
    return bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]

# First pass: collect entities whose any point lies within expanded bbox
group_entities = {}
for ent in msp:
    pts = get_entity_points(ent)
    if not pts:
        continue
    if any(point_in_bbox(p, expanded_bbox) for p in pts):
        group_entities[ent.dxf.handle] = {'handle': ent.dxf.handle, 'type': ent.dxftype(),
                                         'layer': ent.dxf.layer if ent.dxf.hasattr('layer') else None,
                                         'bbox': bbox_from_pts(pts)}

# Second pass: connectivity – add any entity that shares a point with already collected ones
changed = True
while changed:
    changed = False
    existing_points = set()
    for info in group_entities.values():
        pts = info['bbox']
        if pts:
            # store four corners as points for quick check
            existing_points.update([(pts[0], pts[1]), (pts[2], pts[3])])
    for ent in msp:
        h = ent.dxf.handle
        if h in group_entities:
            continue
        pts = get_entity_points(ent)
        if not pts:
            continue
        if any(p in existing_points for p in pts):
            group_entities[h] = {'handle': h, 'type': ent.dxftype(),
                                 'layer': ent.dxf.layer if ent.dxf.hasattr('layer') else None,
                                 'bbox': bbox_from_pts(pts)}
            changed = True

# 4. Compute overall extents of the group
all_bboxes = [info['bbox'] for info in group_entities.values() if info['bbox']]
min_x = min(b[0] for b in all_bboxes)
min_y = min(b[1] for b in all_bboxes)
max_x = max(b[2] for b in all_bboxes)
max_y = max(b[3] for b in all_bboxes)

# 5. Translation needed for A3 border with 10,000 mm margin
margin = 10000
border_min_x, border_min_y = margin, margin
border_max_x, border_max_y = 420000 - margin, 297000 - margin
shift_x = 0
shift_y = 0
if min_x < border_min_x:
    shift_x = border_min_x - min_x
elif max_x > border_max_x:
    shift_x = border_max_x - max_x
if min_y < border_min_y:
    shift_y = border_min_y - min_y
elif max_y > border_max_y:
    shift_y = border_max_y - max_y

# 6. Verify unrelated layers are not present in group
unrelated_layers = {'ROAD', 'TITLE_BLOCK', 'LEGEND', 'DIMENSION'}
unrelated_in_group = []
for info in group_entities.values():
    if info['layer'] in unrelated_layers:
        unrelated_in_group.append(info['handle'])

# 7. Build report
lines = []
lines.append('--- CAD V11 Layout Correction Third Audit (READ ONLY) ---')
lines.append('')
lines.append('1. Verified handles (type, layer, bbox)')
for h in handles_of_interest:
    info = handle_info.get(h)
    if info is None:
        lines.append(f'   Handle {h}: NOT FOUND')
    else:
        lines.append(f"   Handle {h}: type {info['type']}, layer {info['layer']}, bbox {info['bbox']}")
lines.append('')
lines.append('2. Comparison with earlier audit reports')
for h in handles_of_interest:
    cur = handle_info.get(h)
    prev = prev_data.get(h)
    if cur and prev:
        diff = []
        if cur['type'] != prev['type']:
            diff.append(f"type {prev['type']} -> {cur['type']}")
        if cur['layer'] != prev['layer']:
            diff.append(f"layer {prev['layer']} -> {cur['layer']}")
        if cur['bbox'] != prev['bbox']:
            diff.append(f"bbox {prev['bbox']} -> {cur['bbox']}")
        if diff:
            lines.append(f'   Handle {h}: discrepancies: {", ".join(diff)}')
        else:
            lines.append(f'   Handle {h}: no discrepancy with previous audit')
    else:
        lines.append(f'   Handle {h}: no previous data to compare')
lines.append('')
lines.append('3. Complete enlarged-detail group entities')
lines.append('   Handle | Type | Layer | BBox (xmin, ymin, xmax, ymax)')
for h in sorted(group_entities, key=lambda x: int(x,16)):
    e = group_entities[h]
    lines.append(f"   {h:>6} | {e['type']:<12} | {e['layer']:<12} | ({e['bbox'][0]:.0f}, {e['bbox'][1]:.0f}, {e['bbox'][2]:.0f}, {e['bbox'][3]:.0f})")
lines.append('')
lines.append('4. Overall group extents')
lines.append(f'   Min X: {min_x:.0f} mm')
lines.append(f'   Min Y: {min_y:.0f} mm')
lines.append(f'   Max X: {max_x:.0f} mm')
lines.append(f'   Max Y: {max_y:.0f} mm')
lines.append('')
lines.append('5. Translation required to fit within A3 border with 10,000 mm margin')
lines.append(f'   Target interior X: [{border_min_x} - {border_max_x}]')
lines.append(f'   Target interior Y: [{border_min_y} - {border_max_y}]')
lines.append(f'   Required shift: ΔX = {shift_x:.0f} mm, ΔY = {shift_y:.0f} mm')
lines.append('')
lines.append('6. Unrelated layers present in group')
if unrelated_in_group:
    lines.append(f'   WARNING: Handles on main-road layers found: {", ".join(unrelated_in_group)}')
else:
    lines.append('   None – group contains only detail‑specific layers')
lines.append('')
lines.append('7. Validation of translation')
new_min_x = min_x + shift_x
new_max_x = max_x + shift_x
new_min_y = min_y + shift_y
new_max_y = max_y + shift_y
lines.append(f'   After translation: X [{new_min_x:.0f}, {new_max_x:.0f}], Y [{new_min_y:.0f}, {new_max_y:.0f}]')
valid = (border_min_x <= new_min_x <= border_max_x and border_min_x <= new_max_x <= border_max_x and
         border_min_y <= new_min_y <= border_max_y and border_min_y <= new_max_y <= border_max_y)
lines.append(f'   Fits within required area: {'PASS' if valid else 'FAIL'}')
lines.append('')
lines.append('--- END OF THIRD AUDIT ---')

# Write report
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('Report written to', report_path)
