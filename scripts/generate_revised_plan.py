import ezdxf, json, os
from pathlib import Path

project_root = Path(r"C:\\final year\\Traffic_Calming_Road_Safety")

v10_path = project_root / "drawings" / "02_proposed_traffic_calming_road_v10.dxf"
report_path = project_root / "reports" / "cad_v11_layout_correction_revised_plan.txt"

doc = ezdxf.readfile(str(v10_path))
entitydb = doc.entitydb
msp = doc.modelspace()

# Helper to get points of an entity
def get_points(ent):
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

def bbox_from_points(pts):
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))

# Handles of interest
interest_handles = ['1C2', '1BB', '1BE', '1BF', '1C0', '243', '245']

# Gather layers of these handles
layers_of_interest = set()
for h in interest_handles:
    ent = entitydb.get(h)
    if ent:
        layer = ent.dxf.layer if ent.dxf.hasattr('layer') else None
        layers_of_interest.add(layer)
        # Also collect any block name if INSERT
        if ent.dxftype() == 'INSERT':
            # get block name
            layers_of_interest.add(ent.dxf.name)

# Also include layer named 'DETAIL' if present
layers_of_interest.add('DETAIL')

# Identify candidate entities: those whose layer is in layers_of_interest
candidates = []
for ent in msp:
    layer = ent.dxf.layer if ent.dxf.hasattr('layer') else None
    if layer in layers_of_interest:
        pts = get_points(ent)
        if not pts:
            continue
        bbox = bbox_from_points(pts)
        candidates.append({'handle': ent.dxf.handle, 'type': ent.dxftype(), 'layer': layer, 'bbox': bbox, 'points': pts})

# Additionally, include any entity that is close to the main detail outline (handle 1C2)
outline_ent = entitydb.get('1C2')
outline_bbox = None
if outline_ent:
    outline_bbox = bbox_from_points(get_points(outline_ent))

# Determine a generous expansion of outline bbox to catch extensions (e.g., 5000 mm each side)
if outline_bbox:
    expand = 5000
    expanded = (outline_bbox[0]-expand, outline_bbox[1]-expand, outline_bbox[2]+expand, outline_bbox[3]+expand)
else:
    expanded = None

# Add any entity whose any point lies within the expanded bbox (even if layer not in set)
if expanded:
    for ent in msp:
        if any(e['handle']==ent.dxf.handle for e in candidates):
            continue
        pts = get_points(ent)
        if not pts:
            continue
        for p in pts:
            if expanded[0] <= p[0] <= expanded[2] and expanded[1] <= p[1] <= expanded[3]:
                bbox = bbox_from_points(pts)
                candidates.append({'handle': ent.dxf.handle, 'type': ent.dxftype(), 'layer': ent.dxf.layer if ent.dxf.hasattr('layer') else None, 'bbox': bbox, 'points': pts})
                break

# Remove duplicates by handle
unique = {}
for e in candidates:
    unique[e['handle']] = e
detail_entities = list(unique.values())

# Compute overall extents of the detail group
all_min_x = min(e['bbox'][0] for e in detail_entities if e['bbox'])
all_min_y = min(e['bbox'][1] for e in detail_entities if e['bbox'])
all_max_x = max(e['bbox'][2] for e in detail_entities if e['bbox'])
all_max_y = max(e['bbox'][3] for e in detail_entities if e['bbox'])

# Translation needed for A3 border with 10000 mm margin
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

# Verify unrelated elements (main road plan, title block, legend) are not in detail_entities
key_layers = {'ROAD', 'TITLE_BLOCK', 'LEGEND', 'DIMENSION'}
unrelated_overlap = False
for e in detail_entities:
    if e['layer'] in key_layers:
        unrelated_overlap = True
        break

# Build report
lines = []
lines.append('--- CAD V11 Layout Correction Revised Plan (READ ONLY) ---')
lines.append('')
lines.append('1. Handles of interest and their layers')
for h in interest_handles:
    ent = entitydb.get(h)
    if ent:
        layer = ent.dxf.layer if ent.dxf.hasattr('layer') else 'None'
        lines.append(f'   Handle {h}: type {ent.dxftype()}, layer {layer}')
    else:
        lines.append(f'   Handle {h}: NOT FOUND')
lines.append('')
lines.append('2. All identified detail-group entities')
lines.append('   Handle | Type | Layer | BBox (xmin, ymin, xmax, ymax)')
for e in sorted(detail_entities, key=lambda x: int(x['handle'],16)):
    bbox = e['bbox']
    lines.append(f"   {e['handle']:>6} | {e['type']:<12} | {e['layer']:<12} | ({bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f})")
lines.append('')
lines.append('3. Overall detail group extents')
lines.append(f'   Min X: {all_min_x:.0f} mm')
lines.append(f'   Min Y: {all_min_y:.0f} mm')
lines.append(f'   Max X: {all_max_x:.0f} mm')
lines.append(f'   Max Y: {all_max_y:.0f} mm')
lines.append('')
lines.append('4. Translation required to fit within A3 border with 10,000 mm margin')
lines.append(f'   Target interior X: [{border_min_x} - {border_max_x}]')
lines.append(f'   Target interior Y: [{border_min_y} - {border_max_y}]')
lines.append(f'   Required shift: ΔX = {shift_x:.0f} mm, ΔY = {shift_y:.0f} mm')
lines.append('')
lines.append('5. Impact on unrelated elements')
lines.append(f'   Any detail entity on main-road or title-block layers? {'YES' if unrelated_overlap else 'NO'}')
lines.append('')
lines.append('--- END OF PLAN ---')

with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('Report written to', report_path)
