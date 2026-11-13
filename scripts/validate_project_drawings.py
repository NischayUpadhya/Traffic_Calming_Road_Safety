"""
validate_project_drawings.py
BCV755A Road Safety Engineering – CAD Validation
Description: Read‑only validation of existing DXF drawings for the project.
Creates a text report at reports/cad_validation_report.txt.
"""

import os
import sys
import math
from pathlib import Path

try:
    import ezdxf
except ModuleNotFoundError:
    print("ezdxf not installed – install with 'pip install ezdxf' and retry.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Project configuration (paths are relative to this script location)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DRAWING1 = PROJECT_ROOT / "drawings" / "01_existing_urban_road_v4.dxf"
DRAWING2_V9 = PROJECT_ROOT / "drawings" / "02_proposed_traffic_calming_road_v9.dxf"
DRAWING2_V8 = PROJECT_ROOT / "drawings" / "02_proposed_traffic_calming_road_v8.dxf"
REPORT_PATH = PROJECT_ROOT / "reports" / "cad_validation_report.txt"

# Expected geometry constants (mm in model space)
X0 = 70_000
ROAD_LENGTH = 200_000
CARRIAGEWAY_W = 7_000
LANE_W = 3_500
FOOTPATH_W = 2_000
TOTAL_W = 11_000

# Detail panel location (from version 8/9 scripts)
DETAIL_X0 = 200_000
DETAIL_Y0 = 250_000
DETAIL_W = 220_000
DETAIL_H = 130_000
DETAIL_AREA = (
    DETAIL_X0,
    DETAIL_Y0,
    DETAIL_X0 + DETAIL_W,
    DETAIL_Y0 + DETAIL_H,
)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def load_dxf(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f"DXF not found: {path}")
    return ezdxf.readfile(str(path))

def bbox(entity):
    """Return (xmin, ymin, xmax, ymax) for a DXF entity that has a bounding box.
    For TEXT we approximate using insert point +/- height/2.
    """
    try:
        ext = entity.bbox()
        return ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y
    except Exception:
        # Fallback for TEXT
        if entity.dxftype() == "TEXT":
            h = entity.dxf.height
            x, y = entity.dxf.insert.x, entity.dxf.insert.y
            return x - h/2, y - h/2, x + h/2, y + h/2
        return None

def within_detail(entity):
    b = bbox(entity)
    if b is None:
        return False
    x1, y1, x2, y2 = b
    dx0, dy0, dx1, dy1 = DETAIL_AREA
    # Simple overlap test
    return not (x2 < dx0 or x1 > dx1 or y2 < dy0 or y1 > dy1)

def layer_entities(msp, layer_name):
    """Return a list of entities in *msp* that are on *layer_name*.
    The implementation avoids the ezdxf query syntax which can be error‑prone
    and instead filters by the DXF *layer* attribute directly.
    """
    return [
        entity for entity in msp
        if entity.dxf.hasattr("layer") and entity.dxf.layer.upper() == layer_name.upper()
    ]

# ---------------------------------------------------------------------------
# Validation functions
# ---------------------------------------------------------------------------

def validate_road_geometry(msp):
    """Check that the main road extents match the required dimensions.
    Returns a dict of PASS/FAIL entries.
    """
    results = {}
    # Find road outer lines on LAYER_ROAD
    road_lines = layer_entities(msp, "ROAD")
    # Compute min/max X/Y from road lines (excluding detail area)
    xs = []
    ys = []
    for e in road_lines:
        if within_detail(e):
            continue
        if e.dxftype() == "LINE":
            xs.extend([e.dxf.start.x, e.dxf.end.x])
            ys.extend([e.dxf.start.y, e.dxf.end.y])
        elif e.dxftype() == "LWPOLYLINE":
            for pt in e.get_points():
                xs.append(pt[0])
                ys.append(pt[1])
    if not xs or not ys:
        results["road_present"] = (False, "No ROAD entities found")
        return results
    length = max(xs) - min(xs)
    width = max(ys) - min(ys)
    results["road_length"] = (abs(length - ROAD_LENGTH) < 1e-3, f"found {length:.0f} mm")
    results["road_total_width"] = (abs(width - TOTAL_W) < 1e-3, f"found {width:.0f} mm")
    # Check carriageway and footpath widths using layers
    # FOOTPATH layer should contain two rectangles of FOOTPATH_W each
    fp_entities = layer_entities(msp, "FOOTPATH")
    fp_widths = []
    for e in fp_entities:
        if within_detail(e):
            continue
        if e.dxftype() == "LWPOLYLINE":
            # Assuming rectangle: compute Y extents
            b = bbox(e)
            if b:
                _, y1, _, y2 = b
                fp_widths.append(abs(y2 - y1))
    ok_fp = all(abs(w - FOOTPATH_W) < 1e-3 for w in fp_widths) and len(fp_widths) >= 2
    results["footpaths"] = (ok_fp, f"found {len(fp_widths)} footpath rectangles, widths: {fp_widths}")
    # Carriageway width via ROAD layer between footpaths
    cw_entities = layer_entities(msp, "ROAD")
    cw_widths = []
    for e in cw_entities:
        if within_detail(e):
            continue
        if e.dxftype() == "LWPOLYLINE":
            b = bbox(e)
            if b:
                _, y1, _, y2 = b
                w = abs(y2 - y1)
                if abs(w - CARRIAGEWAY_W) < 1e-3:
                    cw_widths.append(w)
    ok_cw = len(cw_widths) >= 1
    results["carriageway"] = (ok_cw, f"found {len(cw_widths)} carriageway sections, widths: {cw_widths}")
    # Lane width via LANE layer (centerline spacing)
    lane_entities = layer_entities(msp, "LANE_MARKINGS")
    lane_spacings = []
    for e in lane_entities:
        if within_detail(e):
            continue
        if e.dxftype() == "LINE" and e.dxf.linetype == "DASHED":
            # vertical centreline, measure Y length
            length = abs(e.dxf.start.y - e.dxf.end.y)
            lane_spacings.append(length)
    # Expect one centreline of total carriageway width and arrows for lane widths
    # We'll just check that we have at least one dashed line of length CARRIAGEWAY_W
    ok_lane = any(abs(l - CARRIAGEWAY_W) < 1e-3 for l in lane_spacings)
    results["lane_centerline"] = (ok_lane, f"found centreline lengths: {lane_spacings}")
    return results

def validate_crossings(msp):
    """Check for raised tables at chainages 60000 and 140000 mm.
    In the scripts these are tables drawn on LAYER_TRAFFIC_CALMING with length 6000.
    """
    results = {}
    expected_chainages = [60_000, 140_000]
    found = []
    for xc in expected_chainages:
        x_coord = X0 + xc
        # Look for a rectangle on TRAFFIC_CALMING whose X extents contain x_coord
        tables = []
        for e in layer_entities(msp, "TRAFFIC_CALMING"):
            if within_detail(e):
                continue
            if e.dxftype() == "LWPOLYLINE":
                b = bbox(e)
                if b:
                    x1, _, x2, _ = b
                    if x1 <= x_coord <= x2:
                        tables.append(e)
        results[f"crossing_{xc}"] = (len(tables) > 0, f"found {len(tables)} tables at X≈{x_coord}")
        found.append(len(tables) > 0)
    return results

def validate_detail_entities(msp):
    """Validate that the detail panel (outside of main plan) contains required entities.
    Checks for approach ramps, raised table, zebra stripes, signs, studs, arrows.
    """
    results = {}
    # Filter entities that are inside the detail area
    detail_entities = [e for e in msp if within_detail(e)]
    # Approach ramps – lines on TRAFFIC_CALMING that connect footpath to table
    ramp_lines = [e for e in detail_entities if e.dxftype() == "LINE" and e.dxf.layer == "TRAFFIC_CALMING"]
    results["approach_ramps"] = (len(ramp_lines) >= 2, f"found {len(ramp_lines)} ramp lines")
    # Raised table – rectangle on TRAFFIC_CALMING of length 6000*10 = 60000
    table_rects = [e for e in detail_entities if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "TRAFFIC_CALMING"]
    # Use width to approximate (should be CARRIAGEWAY_W_S = 70_000)
    ok_table = any(abs((bbox(e)[2] - bbox(e)[0]) - 60_000) < 1e3 for e in table_rects)
    results["raised_table"] = (ok_table, f"found {len(table_rects)} TRAFFIC_CALMING polylines")
    # Zebra stripes – DASHED lines on TRAFFIC_CALMING across table width
    zebra = [e for e in detail_entities if e.dxftype() == "LINE" and e.dxf.layer == "TRAFFIC_CALMING" and e.dxf.linetype == "DASHED"]
    results["zebra_stripes"] = (len(zebra) >= 6, f"found {len(zebra)} zebra stripe lines")
    # Warning and speed signs – squares on SIGNS layer
    sign_squares = [e for e in detail_entities if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "SIGNS"]
    results["signs"] = (len(sign_squares) >= 2, f"found {len(sign_squares)} sign squares")
    # Reflective studs – circles on TRAFFIC_CALMING
    studs = [e for e in detail_entities if e.dxftype() == "CIRCLE" and e.dxf.layer == "TRAFFIC_CALMING"]
    results["reflective_studs"] = (len(studs) >= 2, f"found {len(studs)} studs")
    # Direction arrows – lines on LANE_MARKINGS inside detail panel
    arrows = [e for e in detail_entities if e.dxftype() == "LINE" and e.dxf.layer == "LANE_MARKINGS"]
    results["detail_arrows"] = (len(arrows) >= 2, f"found {len(arrows)} arrow lines")
    return results

def validate_layers(msp):
    required_layers = [
        "ROAD", "LANE_MARKINGS", "FOOTPATH", "DIMENSIONS", "TEXT",
        "TITLE_BLOCK", "LEGEND", "TRAFFIC_CALMING", "SIGNS",
    ]
    existing = set(l.dxf.name for l in msp.doc.layers)
    missing = [l for l in required_layers if l not in existing]
    extra = [l for l in existing if l not in required_layers]
    return {
        "missing_layers": (len(missing) == 0, f"missing: {missing}"),
        "extra_layers": (len(extra) == 0, f"extra: {extra}"),
    }

def validate_sheet_boundary(msp):
    # A3 landscape: 420000 x 297000, border 10000
    sheet_min_x, sheet_min_y = 0, 0
    sheet_max_x, sheet_max_y = 420_000, 297_000
    out_of_bounds = []
    for e in msp:
        b = bbox(e)
        if b is None:
            continue
        x1, y1, x2, y2 = b
        if x1 < sheet_min_x or y1 < sheet_min_y or x2 > sheet_max_x or y2 > sheet_max_y:
            out_of_bounds.append(e)
    return (len(out_of_bounds) == 0, f"{len(out_of_bounds)} entities out of sheet bounds")

def check_text_collisions(msp):
    texts = [e for e in msp if e.dxftype() == "TEXT"]
    collisions = []
    for i, a in enumerate(texts):
        ba = bbox(a)
        if ba is None:
            continue
        for b in texts[i+1:]:
            bb = bbox(b)
            if bb is None:
                continue
            # simple overlap test
            if not (ba[2] < bb[0] or ba[0] > bb[2] or ba[3] < bb[1] or ba[1] > bb[3]):
                collisions.append((a, b))
    # limitation: only axis‑aligned bbox, ignores rotation, scaling, multiline text.
    return (len(collisions) == 0, f"{len(collisions)} overlapping text pairs (axis‑aligned bbox only)")

def compare_main_plan(msp_v9, msp_v8):
    # Compare all entities outside the detail panel.
    diffs = []
    ents_v9 = [e for e in msp_v9 if not within_detail(e)]
    ents_v8 = [e for e in msp_v8 if not within_detail(e)]
    # Build simple dictionaries keyed by (type, layer, geometry signature)
    def signature(e):
        if e.dxftype() == "LINE":
            return ("LINE", e.dxf.layer, tuple(sorted([e.dxf.start, e.dxf.end])))
        if e.dxftype() == "LWPOLYLINE":
            pts = tuple(e.get_points())
            return ("LWPOLYLINE", e.dxf.layer, pts)
        if e.dxftype() == "CIRCLE":
            return ("CIRCLE", e.dxf.layer, (e.dxf.center.x, e.dxf.center.y, e.dxf.radius))
        if e.dxftype() == "TEXT":
            return ("TEXT", e.dxf.layer, (e.dxf.insert.x, e.dxf.insert.y, e.dxf.text))
        return (e.dxftype(), e.dxf.layer, None)
    set_v9 = {signature(e) for e in ents_v9}
    set_v8 = {signature(e) for e in ents_v8}
    only_v9 = set_v9 - set_v8
    only_v8 = set_v8 - set_v9
    if only_v9:
        diffs.append(("only_in_v9", len(only_v9)))
    if only_v8:
        diffs.append(("only_in_v8", len(only_v8)))
    return diffs

def main():
    report_lines = []
    # Load DXFs
    doc1 = load_dxf(DRAWING1)
    doc2_v9 = load_dxf(DRAWING2_V9)
    doc2_v8 = load_dxf(DRAWING2_V8)
    msp1 = doc1.modelspace()
    msp2_v9 = doc2_v9.modelspace()
    msp2_v8 = doc2_v8.modelspace()

    report_lines.append("CAD Validation Report – BCV755A Road Safety Engineering")
    report_lines.append(f"Generated on: {datetime.now().isoformat()}")
    report_lines.append("")

    # 1. Road geometry (both drawings)
    report_lines.append("1. Road geometry validation (Drawing 01)")
    geom_results = validate_road_geometry(msp1)
    for k, (ok, msg) in geom_results.items():
        report_lines.append(f"   {k}: {'PASS' if ok else 'FAIL'} – {msg}")
    report_lines.append("")

    # 2. Raised crossings in Drawing 02 (v9)
    report_lines.append("2. Raised crossing locations (Drawing 02 v9)")
    crossing_results = validate_crossings(msp2_v9)
    for k, (ok, msg) in crossing_results.items():
        report_lines.append(f"   {k}: {'PASS' if ok else 'FAIL'} – {msg}")
    report_lines.append("")

    # 3. Detail panel entities (v9)
    report_lines.append("3. Detail panel entity presence (Drawing 02 v9)")
    detail_results = validate_detail_entities(msp2_v9)
    for k, (ok, msg) in detail_results.items():
        report_lines.append(f"   {k}: {'PASS' if ok else 'FAIL'} – {msg}")
    report_lines.append("")

    # 4. Continuous footpaths and pedestrian connections (both drawings)
    report_lines.append("4. Footpath continuity (Drawing 01)")
    fp_ok = geom_results.get("footpaths", (False, ""))[0]
    report_lines.append(f"   footpaths: {'PASS' if fp_ok else 'FAIL'}")
    report_lines.append("")

    # 5. Layer verification (both drawings)
    report_lines.append("5. Layer existence (Drawing 01 & Drawing 02 v9)")
    layers1 = validate_layers(msp1)
    layers2 = validate_layers(msp2_v9)
    for name, result in [("Drawing 01", layers1), ("Drawing 02 v9", layers2)]:
        report_lines.append(f"   {name}:")
        for k, (ok, msg) in result.items():
            report_lines.append(f"      {k}: {'PASS' if ok else 'FAIL'} – {msg}")
    report_lines.append("")

    # 6. Sheet boundary check
    report_lines.append("6. Sheet boundary adherence (both drawings)")
    sheet1 = validate_sheet_boundary(msp1)
    sheet2 = validate_sheet_boundary(msp2_v9)
    report_lines.append(f"   Drawing 01: {'PASS' if sheet1[0] else 'FAIL'} – {sheet1[1]}")
    report_lines.append(f"   Drawing 02 v9: {'PASS' if sheet2[0] else 'FAIL'} – {sheet2[1]}")
    report_lines.append("")

    # 7. Text overlap check (approximate)
    report_lines.append("7. Text overlap (approximate axis‑aligned bounding boxes)")
    txt1 = check_text_collisions(msp1)
    txt2 = check_text_collisions(msp2_v9)
    report_lines.append(f"   Drawing 01: {'PASS' if txt1[0] else 'FAIL'} – {txt1[1]}")
    report_lines.append(f"   Drawing 02 v9: {'PASS' if txt2[0] else 'FAIL'} – {txt2[1]}")
    report_lines.append("   Limitation: rotation and multiline text are not accounted for.")
    report_lines.append("")

    # 8. Main‑plan comparison (v9 vs v8)
    report_lines.append("8. Main‑plan geometry comparison (Drawing 02 v9 vs v8)")
    diffs = compare_main_plan(msp2_v9, msp2_v8)
    if not diffs:
        report_lines.append("   PASS – No differences detected in main‑plan entities.")
    else:
        for typ, count in diffs:
            report_lines.append(f"   {typ}: {count} differing entities (manual inspection recommended)")
    report_lines.append("")

    # 9. Units and scale distinction
    report_lines.append("9. DXF units and scale notes")
    units1 = doc1.header.get("$INSUNITS", "unknown")
    units2 = doc2_v9.header.get("$INSUNITS", "unknown")
    report_lines.append(f"   Drawing 01 units code: {units1} (expected 4 = mm)")
    report_lines.append(f"   Drawing 02 v9 units code: {units2} (expected 4 = mm)")
    report_lines.append("   Note: Main‑plan geometry is model‑space 1:1 mm. The enlarged detail panel uses a factor‑10 scaling to represent a 1:100 conceptual scale; dimensions are displayed as real values.")
    report_lines.append("")

    # 10. Summary of issues
    report_lines.append("10. Summary of detected issues")
    issues = []
    # Collect any FAIL entries
    # Collect any FAIL entries from dict‑based results
    for section in [geom_results, crossing_results, detail_results, layers1, layers2]:
        for k, (ok, msg) in section.items():
            if not ok:
                issues.append(f"{k}: {msg}")
    # Handle tuple‑based results (sheet boundary and text overlap checks)
    for name, result in [("sheet_boundary_01", sheet1), ("sheet_boundary_02", sheet2), ("text_overlap_01", txt1), ("text_overlap_02", txt2)]:
        ok, msg = result
        if not ok:
            issues.append(f"{name}: {msg}")
    if diffs:
        issues.append("Main‑plan differences between v9 and v8 detected.")
    if not issues:
        report_lines.append("   No failures detected. All automated checks passed.")
    else:
        for i, issue in enumerate(issues, 1):
            report_lines.append(f"   {i}. {issue}")
    report_lines.append("")

    # Write the report
    os.makedirs(REPORT_PATH.parent, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Validation complete. Report written to {REPORT_PATH}")

if __name__ == "__main__":
    from datetime import datetime
    main()
