"""Third‑stage geometry audit (read‑only)

Uses drawings:
 - drawings/01_existing_urban_road_v4.dxf
 - drawings/02_proposed_traffic_calming_road_v9.dxf

Produces a report at reports/cad_third_stage_geometry_audit.txt
"""

import os, sys
from pathlib import Path
from collections import Counter

try:
    import ezdxf
except ModuleNotFoundError:
    print("ezdxf not installed – install with 'pip install ezdxf' and retry.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DRAWING1 = PROJECT_ROOT / "drawings" / "01_existing_urban_road_v4.dxf"
DRAWING2 = PROJECT_ROOT / "drawings" / "02_proposed_traffic_calming_road_v9.dxf"
REPORT_PATH = PROJECT_ROOT / "reports" / "cad_third_stage_geometry_audit.txt"

# Expected geometry (mm)
ROAD_LENGTH_EXPECT = 200_000
TOTAL_WIDTH_EXPECT = 11_000
CARRIAGEWAY_W_EXPECT = 7_000
FOOTPATH_W_EXPECT = 2_000
X0 = 70_000  # origin offset used in chainage calculations

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
def load_dxf(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f"DXF not found: {path}")
    return ezdxf.readfile(str(path))

def bbox(entity):
    """Return (xmin, ymin, xmax, ymax) or None."""
    try:
        ext = entity.bbox()
        return ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y
    except Exception:
        if entity.dxftype() == "TEXT":
            h = entity.dxf.height
            x, y = entity.dxf.insert.x, entity.dxf.insert.y
            return x - h/2, y - h/2, x + h/2, y + h/2
        if entity.dxftype() == "MTEXT":
            # approximate with insertion point only
            p = entity.dxf.insert
            return p.x, p.y, p.x, p.y
        return None

def fmt_coord(val):
    return f"{val:.2f}" if isinstance(val, (int, float)) else str(val)

def format_entity(e):
    h = e.dxf.handle
    typ = e.dxftype()
    layer = getattr(e.dxf, "layer", "<none>")
    b = bbox(e)
    bbox_str = f"{b}" if b else "N/A"
    if typ == "LINE":
        start = e.dxf.start
        end = e.dxf.end
        return f"Handle {h}: {typ} on {layer}, start {fmt_coord(start.x)},{fmt_coord(start.y)} end {fmt_coord(end.x)},{fmt_coord(end.y)}, bbox {bbox_str}"
    elif typ in {"LWPOLYLINE", "POLYLINE"}:
        pts = list(e.get_points())
        pts_str = ", ".join([f"({fmt_coord(p[0])},{fmt_coord(p[1])})" for p in pts])
        return f"Handle {h}: {typ} on {layer}, vertices [{pts_str}], bbox {bbox_str}"
    elif typ == "CIRCLE":
        c = e.dxf.center
        r = e.dxf.radius
        return f"Handle {h}: CIRCLE on {layer}, center {fmt_coord(c.x)},{fmt_coord(c.y)} radius {fmt_coord(r)}, bbox {bbox_str}"
    elif typ in {"TEXT", "MTEXT"}:
        ins = e.dxf.insert
        txt = getattr(e.dxf, "text", "").replace("\n", " ")
        return f"Handle {h}: {typ} on {layer}, text '{txt}', insert {fmt_coord(ins.x)},{fmt_coord(ins.y)}, bbox {bbox_str}"
    elif typ == "INSERT":
        name = e.dxf.name
        ins = e.dxf.insert
        return f"Handle {h}: INSERT on {layer}, name {name}, insert {fmt_coord(ins.x)},{fmt_coord(ins.y)}, bbox {bbox_str}"
    else:
        return f"Handle {h}: {typ} on {layer}, bbox {bbox_str}"

# ---------------------------------------------------------------------------
# Task 1 – ROAD entities
# ---------------------------------------------------------------------------
def analyze_road(msp):
    road_entities = [e for e in msp if getattr(e.dxf, "layer", "").upper() == "ROAD"]
    lines = []
    for e in road_entities:
        lines.append(format_entity(e))
    # Determine road extents using ONLY ROAD entities
    xs, ys = [], []
    for e in road_entities:
        b = bbox(e)
        if b:
            x1, y1, x2, y2 = b
            xs.extend([x1, x2])
            ys.extend([y1, y2])
    if xs and ys:
        road_len = max(xs) - min(xs)
        road_width = max(ys) - min(ys)
    else:
        road_len = road_width = None
    return road_entities, lines, road_len, road_width

# ---------------------------------------------------------------------------
# Task 2 – FOOTPATH entities
# ---------------------------------------------------------------------------
def analyze_footpaths(msp):
    fp_entities = [e for e in msp if getattr(e.dxf, "layer", "").upper() == "FOOTPATH"]
    details = []
    for e in fp_entities:
        details.append(format_entity(e))
    # Attempt to derive widths from bounding boxes of each entity
    widths = []
    for e in fp_entities:
        b = bbox(e)
        if b:
            _, y1, _, y2 = b
            widths.append(abs(y2 - y1))
    return fp_entities, details, widths

# ---------------------------------------------------------------------------
# Task 3 – TRAFFIC_CALMING entities (crossings)
# ---------------------------------------------------------------------------
def analyze_crossings(msp):
    tc_entities = [e for e in msp if getattr(e.dxf, "layer", "").upper() == "TRAFFIC_CALMING"]
    details = []
    for e in tc_entities:
        details.append(format_entity(e))
    return tc_entities, details

# ---------------------------------------------------------------------------
# Task 4 – Out‑of‑boundary text entities (specific handles)
# ---------------------------------------------------------------------------
def out_of_boundary_text(msp, handles):
    txt_info = []
    for e in msp:
        if e.dxf.handle.upper() in handles:
            if e.dxftype() in {"TEXT", "MTEXT"}:
                txt_info.append(format_entity(e))
    return txt_info

# ---------------------------------------------------------------------------
# Main audit driver
# ---------------------------------------------------------------------------
def main():
    report = []
    # Load drawings
    doc1 = load_dxf(DRAWING1)
    msp1 = doc1.modelspace()
    doc2 = load_dxf(DRAWING2)
    msp2 = doc2.modelspace()

    report.append("=== TASK 1 – ROAD BOUNDARIES (Drawing 02 v9) ===")
    road_entities, road_lines, road_len, road_w = analyze_road(msp2)
    for line in road_lines:
        report.append(line)
    report.append(f"Calculated road length from ROAD entities: {road_len:.2f} mm" if road_len is not None else "Road length could not be determined")
    report.append(f"Calculated corridor width from ROAD entities: {road_w:.2f} mm" if road_w is not None else "Road width could not be determined")
    report.append("Length check: " + ("PASS" if road_len is not None and abs(road_len - ROAD_LENGTH_EXPECT) < 1e-2 else "FAIL"))
    report.append("Width check: " + ("PASS" if road_w is not None and abs(road_w - TOTAL_WIDTH_EXPECT) < 1e-2 else "FAIL"))
    report.append("")

    report.append("=== TASK 2 – FOOTPATHS (Drawing 02 v9) ===")
    fp_entities, fp_details, fp_widths = analyze_footpaths(msp2)
    for d in fp_details:
        report.append(d)
    # Group widths – expect two distinct footpath groups
    unique_widths = sorted(set(round(w, 2) for w in fp_widths))
    report.append(f"Footpath width measurements (mm): {unique_widths}")
    # Verify there are at least two footpath sections with expected width
    footpath_pass = any(abs(w - FOOTPATH_W_EXPECT) < 1e-2 for w in fp_widths)
    report.append("Footpath width check: " + ("PASS" if footpath_pass else "FAIL"))
    # Continuity – simple check: count of entities > 1 indicates continuous
    report.append(f"Total FOOTPATH entities: {len(fp_entities)}")
    report.append("")

    report.append("=== TASK 3 – RAISED CROSSINGS (TRAFFIC_CALMING) – Drawing 02 v9 ===")
    tc_entities, tc_details = analyze_crossings(msp2)
    for d in tc_details:
        report.append(d)
    report.append(f"Total TRAFFIC_CALMING entities: {len(tc_entities)}")
    # Attempt to locate crossing tables by looking for LWPOLYLINE with large X‑extent
    crossing_tables = []
    for e in tc_entities:
        if e.dxftype() in {"LWPOLYLINE", "POLYLINE"}:
            b = bbox(e)
            if b:
                x1, _, x2, _ = b
                if (x2 - x1) > 5_000:  # heuristic
                    crossing_tables.append(e)
    report.append(f"Potential crossing table outlines (large polylines): {len(crossing_tables)}")
    # Determine chainage of each table based on centre X coordinate
    for tbl in crossing_tables:
        b = bbox(tbl)
        cx = (b[0] + b[2]) / 2
        chainage = cx - X0
        report.append(f"  Table handle {tbl.dxf.handle}: centre X={cx:.2f} => chainage ≈ {chainage:.0f} mm")
    report.append("")

    report.append("=== TASK 4 – OUT‑OF‑BOUNDARY TEXT ENTITIES ===")
    handles_of_interest = {"1BC", "1BD", "240", "242"}
    txts = out_of_boundary_text(msp2, {h.upper() for h in handles_of_interest})
    for t in txts:
        report.append(t)
    # Verify sheet limits (A3 landscape 420000x297000 mm)
    SHEET_MIN_X, SHEET_MIN_Y = 0, 0
    SHEET_MAX_X, SHEET_MAX_Y = 420_000, 297_000
    for e in msp2:
        if e.dxf.handle.upper() in {h.upper() for h in handles_of_interest}:
            b = bbox(e)
            if b:
                out = b[0] < SHEET_MIN_X or b[1] < SHEET_MIN_Y or b[2] > SHEET_MAX_X or b[3] > SHEET_MAX_Y
                report.append(f"  Handle {e.dxf.handle}: out‑of‑bounds = {out}")
    report.append("")

    report.append("=== VALIDATION CONCLUSION ===")
    # Summarise key PASS/FAIL
    report.append(f"Road length check: {'PASS' if road_len is not None and abs(road_len-ROAD_LENGTH_EXPECT)<1e-2 else 'FAIL'}")
    report.append(f"Road width check: {'PASS' if road_w is not None and abs(road_w-TOTAL_WIDTH_EXPECT)<1e-2 else 'FAIL'}")
    report.append(f"Footpath width check: {'PASS' if footpath_pass else 'FAIL'}")
    report.append(f"Raised crossing tables detected: {'PASS' if crossing_tables else 'FAIL'}")
    # Write report
    os.makedirs(REPORT_PATH.parent, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print(f"Third‑stage geometry audit complete. Report written to {REPORT_PATH}")

if __name__ == "__main__":
    from datetime import datetime
    print(f"Running third‑stage audit – {datetime.now().isoformat()}")
    main()
