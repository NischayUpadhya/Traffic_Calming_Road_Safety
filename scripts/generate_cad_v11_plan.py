import ezdxf, json, os
from pathlib import Path

project_root = Path(r"C:\\final year\\Traffic_Calming_Road_Safety")

drawings_dir = project_root / "drawings"
reports_dir = project_root / "reports"

v10_path = drawings_dir / "02_proposed_traffic_calming_road_v10.dxf"
report_path = reports_dir / "cad_v11_layout_correction_plan.txt"

# Load DXF
doc = ezdxf.readfile(str(v10_path))
msp = doc.modelspace()
entitydb = doc.entitydb

# Helper to extract geometry points and bbox
def get_points(ent):
    typ = ent.dxftype()
    if typ == 'LINE':
        return [(ent.dxf.start.x, ent.dxf.start.y), (ent.dxf.end.x, ent.dxf.end.y)]
    if typ in ('LWPOLYLINE', 'POLYLINE'):
        if typ == 'LWPOLYLINE':
            return [pt[:2] for pt in ent.get_points('xy')]
        else:
            return [(v.dxf.x, v.dxf.y) for v in ent.vertices()]
    if typ in ('CIRCLE', 'ARC'):
        # approximate with center and radius
        return [(ent.dxf.center.x, ent.dxf.center.y)]
    if typ in ('TEXT', 'MTEXT'):
        ins = ent.dxf.insert
        return [(ins.x, ins.y)]
    if typ == 'INSERT':
        ins = ent.dxf.insert
        return [(ins.x, ins.y)]
    return []

def bbox_from_points(pts):
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))

# 1. Extract detail outline entity (handle 1C2)
detail_handle = '1C2'
detail_ent = entitydb.get(detail_handle)
if not detail_ent:
    raise ValueError('Detail outline handle 1C2 not found')
detail_pts = get_points(detail_ent)
detail_bbox = bbox_from_points(detail_pts)
# Ensure we have the four corners (might be closed polyline)
if not detail_bbox:
    raise ValueError('Could not compute bbox for detail outline')

detail_min_x, detail_min_y, detail_max_x, detail_max_y = detail_bbox

# 2. Identify all entities belonging to the enlarged detail
# We consider any entity whose any point lies within the detail bbox (including boundary)

def point_inside_bbox(pt, bbox):
    x, y = pt
    x0, y0, x1, y1 = bbox
    return x0 <= x <= x1 and y0 <= y <= y1

detail_entities = []
for ent in msp:
    h = ent.dxf.handle
    pts = get_points(ent)
    if not pts:
        continue
    if any(point_inside_bbox(p, detail_bbox) for p in pts):
        # Record handle, type, layer, bbox of the entity
        ent_bbox = bbox_from_points(pts)
        layer = ent.dxf.layer if ent.dxf.hasattr('layer') else None
        detail_entities.append({'handle': h, 'type': ent.dxftype(), 'layer': layer, 'bbox': ent_bbox})

# Compute overall bounding box of all these entities (union of their bboxes)
all_min_x = min(e['bbox'][0] for e in detail_entities if e['bbox'])
all_min_y = min(e['bbox'][1] for e in detail_entities if e['bbox'])
all_max_x = max(e['bbox'][2] for e in detail_entities if e['bbox'])
all_max_y = max(e['bbox'][3] for e in detail_entities if e['bbox'])

# 3. Compute translation needed to fit within A3 border with 10000 mm margin
margin = 10000
border_min_x, border_min_y = margin, margin
border_max_x, border_max_y = 420000 - margin, 297000 - margin

shift_x = 0
shift_y = 0
if all_min_x < border_min_x:
    shift_x = border_min_x - all_min_x
elif all_max_x > border_max_x:
    shift_x = border_max_x - all_max_x
if all_min_y < border_min_y:
    shift_y = border_min_y - all_min_y
elif all_max_y > border_max_y:
    shift_y = border_max_y - all_max_y

# 4. Verify unrelated elements remain unchanged (simple check: they are outside detail bbox)
# We'll count entities outside the detail bbox that belong to key layers (ROAD, TITLE_BLOCK, etc.)
key_layers = {'ROAD', 'TITLE_BLOCK', 'LEGEND', 'DIMENSION'}
unchanged = True
for ent in msp:
    layer = ent.dxf.layer if ent.dxf.hasattr('layer') else None
    if layer in key_layers:
        pts = get_points(ent)
        if not pts:
            continue
        if any(point_inside_bbox(p, detail_bbox) for p in pts):
            unchanged = False
            break

# Build report content
lines = []
lines.append('--- CAD V11 Layout Correction Plan (READ ONLY) ---')
lines.append('')
lines.append('1. Enlarged crossing detail identification')
lines.append(f'   Detail outline handle 1C2 bbox: X [{detail_min_x:.0f} - {detail_max_x:.0f}], Y [{detail_min_y:.0f} - {detail_max_y:.0f}]')
lines.append(f'   Number of entities intersecting this bbox: {len(detail_entities)}')
lines.append('')
lines.append('2. Entities belonging to the detail group')
lines.append('   Handle | Type | Layer | Bounding Box (xmin, ymin, xmax, ymax)')
for e in detail_entities:
    bbox = e['bbox']
    lines.append(f"   {e['handle']:>6} | {e['type']:<12} | {e['layer']:<12} | ({bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f})")
lines.append('')
lines.append('3. Overall detail group extents')
lines.append(f'   Minimum X: {all_min_x:.0f} mm')
lines.append(f'   Minimum Y: {all_min_y:.0f} mm')
lines.append(f'   Maximum X: {all_max_x:.0f} mm')
lines.append(f'   Maximum Y: {all_max_y:.0f} mm')
lines.append('')
lines.append('4. Translation needed to fit within A3 border (margin 10,000 mm)')
lines.append(f'   Target interior area: X [{border_min_x} - {border_max_x}], Y [{border_min_y} - {border_max_y}]')
lines.append(f'   Required shift: ΔX = {shift_x:.0f} mm, ΔY = {shift_y:.0f} mm')
lines.append('   (Positive values move right/up, negative move left/down)')
lines.append('')
lines.append('5. Impact on unrelated elements')
lines.append(f'   Verification that main road plan, title block, legend, dimensions etc. are outside the detail bbox: {'PASS' if unchanged else 'FAIL'}')
lines.append('')
lines.append('--- END OF PLAN ---')

# Write report
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('Report written to', report_path)
