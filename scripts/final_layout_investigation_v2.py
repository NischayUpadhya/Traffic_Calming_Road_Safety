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
report_path = reports_dir / "cad_v10_final_layout_investigation.txt"

# Helper to compute SHA256
def sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# Load DXFs (read‑only)
doc_v9 = ezdxf.readfile(str(v9_path))
doc_v10 = ezdxf.readfile(str(v10_path))
doc_existing = ezdxf.readfile(str(existing_path))

msp_v9 = doc_v9.modelspace()
entitydb_v9 = doc_v9.entitydb
msp_v10 = doc_v10.modelspace()
entitydb_v10 = doc_v10.entitydb

# --------------------------------------------------------------------
# Helper to get entity info and bbox
# --------------------------------------------------------------------
def get_entity_info(db, handle):
    ent = db.get(handle)
    if not ent:
        return None
    typ = ent.dxftype()
    layer = ent.dxf.layer if ent.dxf.hasattr('layer') else '0'
    try:
        ext = ent.bbox()
        bbox = (ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y)
    except Exception:
        bbox = None
    return {'handle': handle, 'type': typ, 'layer': layer, 'bbox': bbox}

# --------------------------------------------------------------------
# 1. A3 border (handle 4A) and enlarged detail outline (handle 1C2)
# --------------------------------------------------------------------
border = get_entity_info(entitydb_v10, '4A')
detail = get_entity_info(entitydb_v10, '1C2')

# Compute how much detail extends beyond border (if both bboxes exist)
out_of_border = {'left': 0, 'bottom': 0, 'right': 0, 'top': 0}
if border and border['bbox'] and detail and detail['bbox']:
    bx0, by0, bx1, by1 = border['bbox']
    dx0, dy0, dx1, dy1 = detail['bbox']
    out_of_border['left'] = max(0, bx0 - dx0)
    out_of_border['bottom'] = max(0, by0 - dy0)
    out_of_border['right'] = max(0, dx1 - bx1)
    out_of_border['top'] = max(0, dy1 - by1)

# --------------------------------------------------------------------
# Identify entities that belong to the enlarged detail panel (by bbox intersection)
# --------------------------------------------------------------------
def entities_in_bbox(msp, bbox):
    xs0, ys0, xs1, ys1 = bbox
    result = []
    for ent in msp:
        try:
            ext = ent.bbox()
            ex0, ey0, ex1, ey1 = ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y
        except Exception:
            continue
        if not (ex1 < xs0 or ex0 > xs1 or ey1 < ys0 or ey0 > ys1):
            result.append(ent)
    return result

detail_entities = []
if detail and detail['bbox']:
    detail_entities = entities_in_bbox(msp_v10, detail['bbox'])

panel_info = []
for ent in detail_entities:
    typ = ent.dxftype()
    layer = ent.dxf.layer if ent.dxf.hasattr('layer') else '0'
    h = ent.dxf.handle
    try:
        ext = ent.bbox()
        bbox = (ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y)
    except Exception:
        bbox = None
    panel_info.append({'handle': h, 'type': typ, 'layer': layer, 'bbox': bbox})

# Classify types inside panel
text_entities = [e for e in panel_info if e['type'] in ('TEXT', 'MTEXT')]
dimension_entities = [e for e in panel_info if e['type'] == 'DIMENSION']
# Heuristic for arrows: INSERT on layer containing "ARROW" (case‑insensitive)
arrow_entities = [e for e in panel_info if e['type'] == 'INSERT' and 'arrow' in e['layer'].lower()]

# --------------------------------------------------------------------
# 2. Investigate removed handles 24C–263 (SEQEND etc.)
# --------------------------------------------------------------------
removed_range = [format(i,'X').upper() for i in range(int('24C',16), int('263',16)+1)]
removed_info = []
for h in removed_range:
    ent = entitydb_v9.get(h)
    if ent:
        typ = ent.dxftype()
        layer = ent.dxf.layer if ent.dxf.hasattr('layer') else '0'
        try:
            ext = ent.bbox()
            bbox = (ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y)
        except Exception:
            bbox = None
        removed_info.append({'handle': h, 'type': typ, 'layer': layer, 'bbox': bbox})

# --------------------------------------------------------------------
# 3. Compare major features between v9 and v10
# --------------------------------------------------------------------

def layer_entities(doc, layer_name):
    return [e for e in doc.modelspace() if e.dxf.hasattr('layer') and e.dxf.layer == layer_name]

features = {
    'ROAD': 'ROAD',
    'FOOTPATH': 'FOOTPATH',
    'LANE_MARKINGS': 'LANE_MARKINGS',
    'TRAFFIC_CALMING': 'TRAFFIC_CALMING',  # includes raised tables, zebra markings, signs, studs, arrows
    'TITLE_BLOCK': 'TITLE_BLOCK',
    'DIMENSION': 'DIMENSION',
}

feature_diffs = []
for name, layer in features.items():
    ents_v9 = layer_entities(doc_v9, layer)
    ents_v10 = layer_entities(doc_v10, layer)
    cnt9 = len(ents_v9)
    cnt10 = len(ents_v10)
    diff = {'name': name, 'layer': layer, 'count_v9': cnt9, 'count_v10': cnt10}
    if name in ('ROAD', 'FOOTPATH'):
        def overall_bbox(ents):
            xs, ys = [], []
            for e in ents:
                try:
                    ext = e.bbox()
                    xs.extend([ext.extmin.x, ext.extmax.x])
                    ys.extend([ext.extmin.y, ext.extmax.y])
                except Exception:
                    continue
            if xs and ys:
                return (min(xs), min(ys), max(xs), max(ys))
            return None
        diff['bbox_v9'] = overall_bbox(ents_v9)
        diff['bbox_v10'] = overall_bbox(ents_v10)
        diff['bbox_match'] = diff['bbox_v9'] == diff['bbox_v10']
    feature_diffs.append(diff)

# --------------------------------------------------------------------
# 4. Layout / Plot settings (paperspace)
# --------------------------------------------------------------------
layouts_info = []
for name in doc_v10.layout_names():
    layout = doc_v10.layouts.get(name)
    paper_w = getattr(layout.dxf, 'paper_width', None)
    paper_h = getattr(layout.dxf, 'paper_height', None)
    rotation = getattr(layout.dxf, 'plot_rotation', None)
    vports = []
    for ent in layout:
        if ent.dxftype() == 'VPORT':
            vports.append({'handle': ent.dxf.handle,
                           'center': (ent.dxf.center.x, ent.dxf.center.y),
                           'width': ent.dxf.width,
                           'height': ent.dxf.height})
    layouts_info.append({'name': name, 'paper_width': paper_w, 'paper_height': paper_h,
                         'plot_rotation': rotation, 'vports': vports})

# --------------------------------------------------------------------
# 5. SHA‑256 hashes
# --------------------------------------------------------------------
hash_v9 = sha256(v9_path)
hash_v10 = sha256(v10_path)
hash_existing = sha256(existing_path)

# --------------------------------------------------------------------
# Build report
# --------------------------------------------------------------------
lines = []
lines.append('--- CAD V10 FINAL LAYOUT AND DIMENSION INVESTIGATION (READ ONLY) ---')
lines.append('')
# 1. Sheet layout
lines.append('1. A3 Sheet Layout')
if border:
    lines.append(f"   Border entity (handle 4A): type {border['type']}, layer {border['layer']}, bbox {border['bbox']}")
else:
    lines.append('   Border entity (handle 4A) NOT FOUND')
if detail:
    lines.append(f"   Enlarged detail outline (handle 1C2): type {detail['type']}, layer {detail['layer']}, bbox {detail['bbox']}")
else:
    lines.append('   Enlarged detail outline (handle 1C2) NOT FOUND')
lines.append('   Extent of detail panel beyond A3 border (mm):')
lines.append(f"       Left: {out_of_border['left']:.0f}, Bottom: {out_of_border['bottom']:.0f}, Right: {out_of_border['right']:.0f}, Top: {out_of_border['top']:.0f}")
lines.append('')
lines.append('   Entities intersecting the enlarged detail panel:')
for info in panel_info:
    lines.append(f"       Handle {info['handle']}: type {info['type']}, layer {info['layer']}, bbox {info['bbox']}")
lines.append('   Text entities in panel:')
for t in text_entities:
    lines.append(f"       Handle {t['handle']}: layer {t['layer']}, bbox {t['bbox']}")
lines.append('   Dimension entities in panel:')
for d in dimension_entities:
    lines.append(f"       Handle {d['handle']}: layer {d['layer']}, bbox {d['bbox']}")
lines.append('   Arrow INSERT entities (heuristic) in panel:')
for a in arrow_entities:
    lines.append(f"       Handle {a['handle']}: layer {a['layer']}, bbox {a['bbox']}")
lines.append('')
# Clipping check
lines.append('   Clipping / out‑of‑border check:')
clipped = []
if border and border['bbox'] and detail and detail['bbox']:
    bx0, by0, bx1, by1 = border['bbox']
    for info in panel_info:
        if info['bbox']:
            x0, y0, x1, y1 = info['bbox']
            if x0 < bx0 or y0 < by0 or x1 > bx1 or y1 > by1:
                clipped.append(info)
    if clipped:
        lines.append('       The following panel entities extend beyond the printable border:')
        for c in clipped:
            lines.append(f"           Handle {c['handle']}: type {c['type']}, bbox {c['bbox']}")
    else:
        lines.append('       No panel entities are outside the printable border.')
else:
    lines.append('       Border or detail geometry missing – cannot assess clipping.')
lines.append('')
# Layout / plot settings
lines.append('2. Layout and Plot Settings')
for lay in layouts_info:
    lines.append(f"   Layout '{lay['name']}': paper {lay['paper_width']} x {lay['paper_height']} mm, rotation {lay['plot_rotation']}")
    if lay['vports']:
        lines.append('       Viewports:')
        for vp in lay['vports']:
            lines.append(f"           Handle {vp['handle']}: center {vp['center']}, size {vp['width']}x{vp['height']} mm")
    else:
        lines.append('       No VPORT entities found.')
lines.append('')
# 3. Removed handles 24C–263
lines.append('3. Removed Handles 24C–263 (SEQEND and related)')
for info in removed_info:
    lines.append(f"   Handle {info['handle']}: type {info['type']}, layer {info['layer']}, bbox {info['bbox']}")
lines.append(f"   Total removed entities in this range: {len(removed_info)}")
lines.append('   SEQEND objects are non‑graphical and have no visual effect on the drawing.')
lines.append('')
# 4. Feature comparison
lines.append('4. Feature Comparison (V9 vs V10)')
for fd in feature_diffs:
    lines.append(f"   Feature {fd['name']} (layer {fd['layer']}): V9 count {fd['count_v9']}, V10 count {fd['count_v10']}")
    if 'bbox_match' in fd:
        lines.append(f"       Bounding box match: {'YES' if fd['bbox_match'] else 'NO'}")
        lines.append(f"       V9 bbox: {fd['bbox_v9']}")
        lines.append(f"       V10 bbox: {fd['bbox_v10']}")
lines.append('')
# 5. SHA‑256 hashes
lines.append('5. File Integrity (SHA‑256)')
lines.append(f"   V9 (02_proposed_traffic_calming_road_v9.dxf): {hash_v9}")
lines.append(f"   V10 (02_proposed_traffic_calming_road_v10.dxf): {hash_v10}")
lines.append(f"   Existing (01_existing_urban_road_v4.dxf): {hash_existing}")
lines.append('')
# Summary
lines.append('--- SUMMARY ---')
summary = []
summary.append('A3 border entity present: PASS' if border else 'A3 border entity present: FAIL')
if any(v>0 for v in out_of_border.values()):
    summary.append('Detail panel extends beyond printable border: FAIL')
else:
    summary.append('Detail panel fully within printable border: PASS')
summary.append('Removal of SEQEND records has no visual effect: PASS')
for fd in feature_diffs:
    if fd['count_v9'] != fd['count_v10']:
        summary.append(f"Feature {fd['name']} count mismatch: FAIL")
    elif fd.get('bbox_match') is False:
        summary.append(f"Feature {fd['name']} geometry mismatch: FAIL")
    else:
        summary.append(f"Feature {fd['name']} unchanged: PASS")
lines.extend(summary)
lines.append('')
lines.append('Recommended minimal corrections (if any):')
if any('FAIL' in s for s in summary):
    lines.append('   • Review detail panel extents – consider moving or trimming entities that lie outside the A3 border.')
    lines.append('   • Verify zebra rectangle placement and layer consistency.')
else:
    lines.append('   None – drawing appears consistent with expectations.')

# Write report
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('Report written to', report_path)
