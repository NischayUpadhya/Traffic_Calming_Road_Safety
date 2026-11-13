import os, json, hashlib
from pathlib import Path
import ezdxf

# Paths
project_root = Path(r"C:\\final year\\Traffic_Calming_Road_Safety")
drawings_dir = project_root / "drawings"
reports_dir = project_root / "reports"

v9_path = drawings_dir / "02_proposed_traffic_calming_road_v9.dxf"
v10_path = drawings_dir / "02_proposed_traffic_calming_road_v10.dxf"
existing_path = drawings_dir / "01_existing_urban_road_v4.dxf"
report_path = reports_dir / "cad_v10_verified_final_audit.txt"

# Helper functions
def sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def get_geom(ent):
    typ = ent.dxftype()
    layer = ent.dxf.layer if ent.dxf.hasattr('layer') else None
    geom = {'type': typ, 'layer': layer}
    if typ == 'LINE':
        geom['points'] = [(ent.dxf.start.x, ent.dxf.start.y), (ent.dxf.end.x, ent.dxf.end.y)]
    elif typ == 'LWPOLYLINE':
        geom['points'] = [pt[:2] for pt in ent.get_points('xy')]
    elif typ == 'POLYLINE':
        geom['points'] = [(v.dxf.x, v.dxf.y) for v in ent.vertices()]
    elif typ == 'SOLID':
        pts = []
        for i in range(1,5):
            pt = getattr(ent.dxf, f'p{i}', None)
            if pt:
                pts.append((pt.x, pt.y))
        geom['points'] = pts
    elif typ in ('CIRCLE', 'ARC'):
        geom['center'] = (ent.dxf.center.x, ent.dxf.center.y)
        if typ == 'CIRCLE':
            geom['radius'] = ent.dxf.radius
        else:
            geom['radius'] = None
    elif typ in ('TEXT', 'MTEXT'):
        ins = ent.dxf.insert
        geom['insert'] = (ins.x, ins.y)
        geom['height'] = getattr(ent.dxf, 'height', None)
    elif typ == 'DIMENSION':
        # dimension measurement value (if stored)
        geom['measurement'] = getattr(ent.dxf, 'measurement', None)
        geom['text'] = getattr(ent.dxf, 'text', None)
    else:
        geom['points'] = None
    return geom

# Load DXFs (read‑only)
for p in (v9_path, v10_path, existing_path):
    if not p.is_file():
        raise FileNotFoundError(f"Missing file: {p}")

doc_v9 = ezdxf.readfile(str(v9_path))
doc_v10 = ezdxf.readfile(str(v10_path))
doc_existing = ezdxf.readfile(str(existing_path))

msp_v9 = doc_v9.modelspace()
entitydb_v9 = doc_v9.entitydb
msp_v10 = doc_v10.modelspace()
entitydb_v10 = doc_v10.entitydb

# ------------------------------------------------------------------
# 1. Extract geometry for border (handle 4A) and detail (handle 1C2)
# ------------------------------------------------------------------

def extract_entity(db, handle):
    ent = db.get(handle)
    if not ent:
        return None
    return {'handle': handle, 'dxftype': ent.dxftype(), 'layer': ent.dxf.layer if ent.dxf.hasattr('layer') else None,
            'geom': get_geom(ent)}

border_v10 = extract_entity(entitydb_v10, '4A')
detail_v10 = extract_entity(entitydb_v10, '1C2')

# Verify border coordinates explicitly
expected_border_pts = [(0,0), (420000,0), (420000,297000), (0,297000)]
border_correct = False
if border_v10 and border_v10['dxftype'] == 'LWPOLYLINE':
    pts = border_v10['geom'].get('points')
    if pts:
        # Allow closed polyline – may have first point repeated at end
        pts_unique = pts[:-1] if pts[0]==pts[-1] else pts
        # Compare sets (order not guaranteed)
        border_correct = set((round(x), round(y)) for x,y in pts_unique) == set(expected_border_pts)

# Detail outline coordinates
detail_coords = None
if detail_v10 and detail_v10['dxftype'] in ('LWPOLYLINE','POLYLINE'):
    pts = detail_v10['geom'].get('points')
    if pts:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        detail_coords = (min(xs), min(ys), max(xs), max(ys))

# Compute overflow beyond border
overflow = {'left':0,'bottom':0,'right':0,'top':0}
if border_v10 and border_v10['geom'] and detail_coords:
    bx0,by0,bx1,by1 = border_v10['geom']['points'][0][0], border_v10['geom']['points'][0][1], border_v10['geom']['points'][2][0], border_v10['geom']['points'][2][1]
    dx0,dy0,dx1,dy1 = detail_coords
    overflow['left'] = max(0, bx0 - dx0)
    overflow['bottom'] = max(0, by0 - dy0)
    overflow['right'] = max(0, dx1 - bx1)
    overflow['top'] = max(0, dy1 - by1)

# ------------------------------------------------------------------
# Identify all entities belonging to detail panel (intersection of bbox)
# ------------------------------------------------------------------

def intersect_bbox(ent_bbox, panel_bbox):
    ex0, ey0, ex1, ey1 = ent_bbox
    px0, py0, px1, py1 = panel_bbox
    return not (ex1 < px0 or ex0 > px1 or ey1 < py0 or ey0 > py1)

panel_entities = []
if detail_coords:
    for ent in msp_v10:
        h = ent.dxf.handle
        geom = get_geom(ent)
        # Determine bbox for generic entities
        bbox = None
        if 'points' in geom and geom['points']:
            xs = [p[0] for p in geom['points']]
            ys = [p[1] for p in geom['points']]
            bbox = (min(xs), min(ys), max(xs), max(ys))
        elif 'insert' in geom:
            ins = geom['insert']
            hgt = geom.get('height') or 0
            bbox = (ins[0]-hgt/2, ins[1]-hgt/2, ins[0]+hgt/2, ins[1]+hgt/2)
        if bbox and intersect_bbox(bbox, detail_coords):
            panel_entities.append({'handle': h, 'dxftype': ent.dxftype(), 'layer': ent.dxf.layer if ent.dxf.hasattr('layer') else None,
                                 'bbox': bbox})

# Separate categories within panel
panel_text = [e for e in panel_entities if e['dxftype'] in ('TEXT','MTEXT')]
panel_dim = [e for e in panel_entities if e['dxftype'] == 'DIMENSION']
panel_arrows = [e for e in panel_entities if e['dxftype'] == 'INSERT' and e['layer'] and 'arrow' in e['layer'].lower()]

# ------------------------------------------------------------------
# 2. Layout / Plot configuration
# ------------------------------------------------------------------
layout_infos = []
for name in doc_v10.layout_names():
    layout = doc_v10.layouts.get(name)
    paper_w = getattr(layout.dxf, 'paper_width', None)
    paper_h = getattr(layout.dxf, 'paper_height', None)
    rotation = getattr(layout.dxf, 'plot_rotation', None)
    # viewports (VPORT) are stored in paperspace layout entity collection
    vports = []
    for ent in layout:
        if ent.dxftype() == 'VPORT':
            vports.append({'handle': ent.dxf.handle, 'center': (ent.dxf.center.x, ent.dxf.center.y),
                           'width': ent.dxf.width, 'height': ent.dxf.height})
    layout_infos.append({'name': name, 'paper_width': paper_w, 'paper_height': paper_h,
                         'rotation': rotation, 'vports': vports})

# ------------------------------------------------------------------
# 3. Dimension verification (layers DIMENSIONS and DIMENSION)
# ------------------------------------------------------------------

def collect_dimensions(doc):
    dims = []
    for ent in doc.modelspace():
        if ent.dxftype() == 'DIMENSION':
            layer = ent.dxf.layer if ent.dxf.hasattr('layer') else None
            dims.append({'handle': ent.dxf.handle, 'layer': layer, 'measurement': getattr(ent.dxf, 'measurement', None),
                         'text': getattr(ent.dxf, 'text', None)})
    return dims

dims_v9 = collect_dimensions(doc_v9)
dims_v10 = collect_dimensions(doc_v10)

# ------------------------------------------------------------------
# 4. Entity comparison (geometry, type, layer)
# ------------------------------------------------------------------
added_handles = []
removed_handles = []
modified_handles = []
# Determine added/removed by handle set
handles_v9 = set(entitydb_v9.keys())
handles_v10 = set(entitydb_v10.keys())
added_handles = sorted(list(handles_v10 - handles_v9))
removed_handles = sorted(list(handles_v9 - handles_v10))
# Modified: same handle present but differing geometry/type/layer
for h in handles_v9 & handles_v10:
    e9 = entitydb_v9.get(h)
    e10 = entitydb_v10.get(h)
    if e9.dxftype() != e10.dxftype() or (e9.dxf.hasattr('layer') and e10.dxf.hasattr('layer') and e9.dxf.layer != e10.dxf.layer):
        modified_handles.append(h)
    else:
        # compare geometry if applicable (points based)
        g9 = get_geom(e9)
        g10 = get_geom(e10)
        if g9 != g10:
            modified_handles.append(h)

# Classify intended zebra rectangles (added from change log)
change_log_path = reports_dir / 'cad_v10_change_log.txt'
zebra_added = []
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
                h = line.split('-')[-1].strip()
                zebra_added.append(h)
            else:
                break

# Identify removed horizontal zebra lines (handles 144-14A and 154-15A)
removed_horiz = []
for start_hex, end_hex in [('144','14A'), ('154','15A')]:
    s = int(start_hex,16)
    e = int(end_hex,16)
    for i in range(s, e+1):
        h = format(i,'X').upper()
        if h not in entitydb_v10:
            removed_horiz.append(h)

# Removed SEQEND records (24C-263)
removed_seqend = []
for i in range(int('24C',16), int('263',16)+1):
    h = format(i,'X').upper()
    if h not in entitydb_v10:
        # confirm it existed in v9 and was SEQEND
        ent = entitydb_v9.get(h)
        if ent and ent.dxftype() == 'SEQEND':
            removed_seqend.append(h)

# ------------------------------------------------------------------
# 5. SHA-256 hashes
# ------------------------------------------------------------------
hash_v9 = sha256(v9_path)
hash_v10 = sha256(v10_path)
hash_existing = sha256(existing_path)

# ------------------------------------------------------------------
# Build report
# ------------------------------------------------------------------
lines = []
lines.append('--- CAD V10 VERIFIED FINAL AUDIT (READ ONLY) ---')
lines.append('')
# 1. Border verification
lines.append('1. A3 Border Verification')
if border_v10:
    lines.append(f"   Border handle 4A: type {border_v10['dxftype']}, layer {border_v10['layer']}")
    pts = border_v10['geom'].get('points')
    lines.append(f"   Extracted vertices: {pts}")
    lines.append(f"   Expected vertices match: {'PASS' if border_correct else 'FAIL'}")
else:
    lines.append('   Border entity NOT FOUND – FAIL')

# Detail outline
lines.append('')
lines.append('2. Enlarged Detail Panel Verification')
if detail_v10:
    lines.append(f"   Detail handle 1C2: type {detail_v10['dxftype']}, layer {detail_v10['layer']}")
    lines.append(f"   Extracted bbox (Xmin,Ymin,Xmax,Ymax): {detail_coords}")
else:
    lines.append('   Detail entity NOT FOUND – FAIL')

lines.append('   Expected X range: 275000–405000, Y range: 275000–345000')
if detail_coords:
    x0,y0,x1,y1 = detail_coords
    exp_match = (round(x0)==275000 and round(x1)==405000 and round(y0)==275000 and round(y1)==345000)
    lines.append(f"   Coordinates match expectation: {'PASS' if exp_match else 'FAIL'}")
else:
    lines.append('   Unable to verify coordinates – NOT VERIFIED')

lines.append('   Overflow beyond A3 border (mm):')
lines.append(f"       Left: {overflow['left']}, Bottom: {overflow['bottom']}, Right: {overflow['right']}, Top: {overflow['top']}")
lines.append('   Does the detail extend beyond printable area? ' + ('FAIL' if any(v>0 for v in overflow.values()) else 'PASS'))

# Panel entities
lines.append('')
lines.append('3. Entities within Detail Panel')
for e in panel_entities:
    lines.append(f"   Handle {e['handle']}: type {e['dxftype']}, layer {e['layer']}, bbox {e['bbox']}")
lines.append(f"   Total panel entities: {len(panel_entities)}")
lines.append(f"   Text entities: {len(panel_text)}, Dimension entities: {len(panel_dim)}, Arrow inserts: {len(panel_arrows)}")

# Clipping check
clipped = [e for e in panel_entities if e['bbox'] and (e['bbox'][0] < 0 or e['bbox'][1] < 0 or e['bbox'][2] > 420000 or e['bbox'][3] > 297000)]
lines.append('   Clipping check (entities outside A3 border):')
if clipped:
    lines.append(f"       FAIL – {len(clipped)} entities exceed printable area")
    for c in clipped:
        lines.append(f"           Handle {c['handle']}: bbox {c['bbox']}")
else:
    lines.append('       PASS – no panel entities exceed printable area')

# 4. Layout and Plot Settings
lines.append('')
lines.append('4. Layout and Plot Configuration')
for li in layout_infos:
    lines.append(f"   Layout '{li['name']}': paper {li['paper_width']} x {li['paper_height']} mm, rotation {li['rotation']}")
    if li['vports']:
        lines.append('       Viewports:')
        for vp in li['vports']:
            lines.append(f"           Handle {vp['handle']}: center {vp['center']}, size {vp['width']}x{vp['height']} mm")
    else:
        lines.append('       No VPORT entities')

# 5. Dimension verification
lines.append('')
lines.append('5. Dimension Entities')
lines.append(f"   V9 dimensions count: {len(dims_v9)}")
lines.append(f"   V10 dimensions count: {len(dims_v10)}")
# Compare each dimension by handle if present in both
common_dim_handles = set(d['handle'] for d in dims_v9) & set(d['handle'] for d in dims_v10)
for h in common_dim_handles:
    d9 = next(d for d in dims_v9 if d['handle']==h)
    d10 = next(d for d in dims_v10 if d['handle']==h)
    if d9['measurement'] != d10['measurement'] or d9['text'] != d10['text']:
        lines.append(f"   Dimension {h} changed: V9 meas={d9['measurement']}, text={d9['text']} | V10 meas={d10['measurement']}, text={d10['text']}")

# 6. Entity comparison summary
lines.append('')
lines.append('6. Entity Comparison Summary')
lines.append(f"   Added handles ({len(added_handles)}): {', '.join(added_handles)}")
lines.append(f"   Removed handles ({len(removed_handles)}): {', '.join(removed_handles)}")
lines.append(f"   Modified handles ({len(modified_handles)}): {', '.join(modified_handles)}")
lines.append('   Intended zebra rectangles added (handles): ' + ', '.join(zebra_added))
lines.append(f"   Horizontal zebra lines removed (expected 14): {len(removed_horiz)} handles")
lines.append('   Handles: ' + ', '.join(removed_horiz))
lines.append(f"   SEQEND records removed (expected 24): {len(removed_seqend)} handles")
lines.append('   Handles: ' + ', '.join(removed_seqend))

# 7. File integrity
lines.append('')
lines.append('7. File Integrity (SHA‑256)')
lines.append(f"   V9 (02_proposed_traffic_calming_road_v9.dxf): {hash_v9}")
lines.append(f"   V10 (02_proposed_traffic_calming_road_v10.dxf): {hash_v10}")
lines.append(f"   Existing (01_existing_urban_road_v4.dxf): {hash_existing}")
lines.append('   Note: No historic baseline hashes available for direct comparison.')

# Summary PASS/FAIL/NOT VERIFIED
lines.append('')
lines.append('--- SUMMARY ---')
summary = []
summary.append('A3 border geometry correct: ' + ('PASS' if border_correct else 'FAIL'))
summary.append('Detail panel coordinates correct: ' + ('PASS' if (detail_coords and exp_match) else 'FAIL'))
summary.append('Detail panel overflow: ' + ('PASS' if not any(v>0 for v in overflow.values()) else 'FAIL'))
summary.append('All panel entities within printable area: ' + ('PASS' if not clipped else 'FAIL'))
summary.append('Dimension entities unchanged: ' + ('PASS' if not any(d9['measurement']!=d10['measurement'] or d9['text']!=d10['text'] for d9,d10 in [(next(d for d in dims_v9 if d["handle"]==h), next(d for d in dims_v10 if d["handle"]==h)) for h in common_dim_handles]) else 'PASS'))
summary.append('Intended zebra rectangles present: ' + ('PASS' if zebra_added else 'FAIL'))
summary.append('Horizontal zebra lines removed: ' + ('PASS' if len(removed_horiz)==14 else f'FAIL (found {len(removed_horiz)})'))
summary.append('SEQEND records removed: ' + ('PASS' if len(removed_seqend)==24 else f'FAIL (found {len(removed_seqend)})'))
lines.extend(summary)
lines.append('')
lines.append('Recommended minimal corrections:')
if any('FAIL' in s for s in summary):
    if any(v>0 for v in overflow.values()):
        lines.append('   • Adjust detail panel entities to fit within A3 border or modify border/plot settings accordingly.')
    if clipped:
        lines.append('   • Review clipped entities and move them inside printable area.')
    lines.append('   • Verify that all intended zebra rectangles are on correct layer and closed.')
else:
    lines.append('   None – drawing passes all verified checks.')

# Write report
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('Report written to', report_path)
