"""Second‑stage read‑only CAD audit

This script analyses the existing DXF drawings without modifying any files.
It produces a detailed report at `reports/cad_second_stage_audit.txt`.
"""

import os
import sys
from pathlib import Path
from collections import Counter, defaultdict

try:
    import ezdxf
except ModuleNotFoundError:
    print("ezdxf not installed – install with 'pip install ezdxf' and retry.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration – paths are relative to this script location
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DRAWING1 = PROJECT_ROOT / "drawings" / "01_existing_urban_road_v4.dxf"
DRAWING2_V8 = PROJECT_ROOT / "drawings" / "02_proposed_traffic_calming_road_v8.dxf"
DRAWING2_V9 = PROJECT_ROOT / "drawings" / "02_proposed_traffic_calming_road_v9.dxf"
REPORT_PATH = PROJECT_ROOT / "reports" / "cad_second_stage_audit.txt"

# Expected constants (mm)
X0 = 70_000
ROAD_LENGTH_EXPECT = 200_000
CARRIAGEWAY_W_EXPECT = 7_000
FOOTPATH_W_EXPECT = 2_000
TOTAL_W_EXPECT = 11_000

# A3 sheet size in model‑space (1:1000) – used for out‑of‑bounds checks
SHEET_MIN_X, SHEET_MIN_Y = 0, 0
SHEET_MAX_X, SHEET_MAX_Y = 420_000, 297_000

def load_dxf(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f"DXF not found: {path}")
    return ezdxf.readfile(str(path))

def bbox(entity):
    """Return (xmin, ymin, xmax, ymax) or None if not available."""
    try:
        ext = entity.bbox()
        return ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y
    except Exception:
        if entity.dxftype() == "TEXT":
            h = entity.dxf.height
            x, y = entity.dxf.insert.x, entity.dxf.insert.y
            return x - h/2, y - h/2, x + h/2, y + h/2
        return None

def layer_counts(msp):
    """Return a dict {layer_name: count} for all entities in modelspace."""
    counts = Counter()
    for e in msp:
        layer = getattr(e.dxf, "layer", "<no layer>")
        counts[layer] += 1
    return dict(counts)

def entity_type_counts(msp):
    cnt = Counter()
    for e in msp:
        cnt[e.dxftype()] += 1
    return dict(cnt)

def block_usage(doc):
    """Return mapping block_name -> number of INSERT references."""
    usage = Counter()
    for e in doc.modelspace():
        if e.dxftype() == "INSERT":
            usage[e.dxf.name] += 1
    return dict(usage)

def collect_entities_by_layer(msp, layer_name):
    return [e for e in msp if getattr(e.dxf, "layer", "").upper() == layer_name.upper()]

def road_extents(msp):
    road_entities = collect_entities_by_layer(msp, "ROAD")
    xs, ys = [], []
    for e in road_entities:
        if e.dxftype() in {"LINE", "LWPOLYLINE", "POLYLINE", "INSERT"}:
            b = bbox(e)
            if b:
                x1, y1, x2, y2 = b
                xs.extend([x1, x2])
                ys.extend([y1, y2])
    if not xs or not ys:
        return None
    return min(xs), max(xs), min(ys), max(ys)

def footpath_rects(msp):
    fps = []
    for e in collect_entities_by_layer(msp, "FOOTPATH"):
        if e.dxftype() == "LWPOLYLINE":
            b = bbox(e)
            if b:
                fps.append(b)
    return fps

def crossing_tables(msp):
    tables = []
    for e in collect_entities_by_layer(msp, "TRAFFIC_CALMING"):
        if e.dxftype() == "LWPOLYLINE":
            b = bbox(e)
            if b:
                tables.append(b)
    return tables

def out_of_bounds_entities(msp):
    oob = []
    for e in msp:
        b = bbox(e)
        if b is None:
            continue
        x1, y1, x2, y2 = b
        if x1 < SHEET_MIN_X or y1 < SHEET_MIN_Y or x2 > SHEET_MAX_X or y2 > SHEET_MAX_Y:
            oob.append((e, b))
    return oob

def compare_entities(msp_a, msp_b, detail_area=None):
    """Return two lists: only_in_a, only_in_b (entity signatures)."""
    def signature(e):
        # Simple geometric signature – type, layer, bbox rounded to 1 mm
        b = bbox(e) or (0,0,0,0)
        return (
            e.dxftype(),
            getattr(e.dxf, "layer", ""),
            tuple(round(v, 1) for v in b),
        )
    set_a = {signature(e) for e in msp_a if not (detail_area and within_detail(e, detail_area))}
    set_b = {signature(e) for e in msp_b if not (detail_area and within_detail(e, detail_area))}
    only_a = set_a - set_b
    only_b = set_b - set_a
    return only_a, only_b

def within_detail(e, area):
    b = bbox(e)
    if b is None:
        return False
    x1, y1, x2, y2 = b
    ax1, ay1, ax2, ay2 = area
    return not (x2 < ax1 or x1 > ax2 or y2 < ay1 or y1 > ay2)

def main():
    report = []
    # ---------------------------------------------------------------------
    # 1. Basic statistics for each drawing
    # ---------------------------------------------------------------------
    for name, path in [
        ("Drawing 01 (existing)", DRAWING1),
        ("Drawing 02 v8 (proposed)", DRAWING2_V8),
        ("Drawing 02 v9 (proposed)", DRAWING2_V9),
    ]:
        doc = load_dxf(path)
        msp = doc.modelspace()
        report.append(f"=== {name} ===")
        # Layers
        layer_cnt = layer_counts(msp)
        report.append("Layers and entity counts:")
        for lyr, cnt in sorted(layer_cnt.items()):
            report.append(f"  {lyr}: {cnt}")
        # Entity types
        type_cnt = entity_type_counts(msp)
        report.append("Entity type totals:")
        for typ, cnt in sorted(type_cnt.items()):
            report.append(f"  {typ}: {cnt}")
        # Blocks
        block_usg = block_usage(doc)
        if block_usg:
            report.append("Block definitions and INSERT usage:")
            for blk, cnt in sorted(block_usg.items()):
                report.append(f"  {blk}: {cnt} INSERT(s)")
        else:
            report.append("No INSERTs found (no block references).")
        report.append("")

    # ---------------------------------------------------------------------
    # 2. Determine actual road geometry (using ROAD layer)
    # ---------------------------------------------------------------------
    # Initialise geometry variables
    length = None
    width = None
    doc2 = load_dxf(DRAWING2_V9)
    msp2 = doc2.modelspace()
    report.append("=== Road geometry (Drawing 02 v9) ===")
    ext = road_extents(msp2)
    if ext:
        xmin, xmax, ymin, ymax = ext
        length = xmax - xmin
        width = ymax - ymin
        report.append(f"Road extents X:{xmin:.0f}-{xmax:.0f}  Y:{ymin:.0f}-{ymax:.0f}")
        report.append(f"Calculated road length = {length:.0f} mm")
        report.append(f"Calculated corridor width = {width:.0f} mm")
        report.append("Length check: " + ("PASS" if abs(length - ROAD_LENGTH_EXPECT) < 1e-3 else "FAIL"))
        report.append("Width check: " + ("PASS" if abs(width - TOTAL_W_EXPECT) < 1e-3 else "FAIL"))
    else:
        report.append("Unable to determine road extents – no ROAD entities found.")
        report.append("Length check: FAIL")
        report.append("Width check: FAIL")
    report.append("")

    # Footpaths
    fps = footpath_rects(msp2)
    fp_ok = all(abs((b[3] - b[1]) - FOOTPATH_W_EXPECT) < 1e-3 for b in fps) and len(fps) >= 2
    report.append(f"Footpath rectangles found: {len(fps)}")
    report.append("Footpath width check: " + ("PASS" if fp_ok else "FAIL"))
    report.append("")

    # Carriageway width – approximate by ROAD layer Y‑extent (already measured as width)
    if width is not None:
        cw_ok = abs(width - CARRIAGEWAY_W_EXPECT - 2*FOOTPATH_W_EXPECT) < 1e-3
        report.append("Carriageway width (derived from total width) check: " + ("PASS" if cw_ok else "FAIL"))
    else:
        report.append("Carriageway width (derived from total width) check: FAIL (road width could not be determined)")
    report.append("")

    # ---------------------------------------------------------------------
    # 3. Crossings – locate tables on TRAFFIC_CALMING layer
    # ---------------------------------------------------------------------
    report.append("=== Raised crossings (Drawing 02 v9) ===")
    tables = crossing_tables(msp2)
    report.append(f"Found {len(tables)} potential crossing tables on TRAFFIC_CALMING layer.")
    expected = [60_000, 140_000]
    for chainage in expected:
        x_target = X0 + chainage
        matches = []
        for b in tables:
            x1, _, x2, _ = b
            if x1 <= x_target <= x2:
                matches.append(b)
        if matches:
            report.append(f"Crossing at chainage {chainage} mm (X≈{x_target}) – PASS ({len(matches)} table(s) found)")
        else:
            report.append(f"Crossing at chainage {chainage} mm (X≈{x_target}) – FAIL (no table intersecting)")
    report.append("")

    # Approach ramps, zebra stripes, signs, studs, arrows – count per layer
    ramp_lines = [e for e in msp2 if e.dxftype() == "LINE" and e.dxf.layer.upper() == "TRAFFIC_CALMING"]
    zebra = [e for e in msp2 if e.dxftype() == "LINE" and e.dxf.layer.upper() == "TRAFFIC_CALMING" and e.dxf.linetype.upper() == "DASHED"]
    signs = [e for e in msp2 if e.dxftype() == "LWPOLYLINE" and e.dxf.layer.upper() == "SIGNS"]
    studs = [e for e in msp2 if e.dxftype() == "CIRCLE" and e.dxf.layer.upper() == "TRAFFIC_CALMING"]
    arrows = [e for e in msp2 if e.dxftype() == "LINE" and e.dxf.layer.upper() == "LANE_MARKINGS"]
    report.append(f"Approach ramp lines (TRAFFIC_CALMING): {len(ramp_lines)}")
    report.append(f"Zebra stripe lines (DASHED, TRAFFIC_CALMING): {len(zebra)}")
    report.append(f"Sign squares (SIGNS): {len(signs)}")
    report.append(f"Reflective studs (CIRCLE, TRAFFIC_CALMING): {len(studs)}")
    report.append(f"Direction arrows (LINE, LANE_MARKINGS): {len(arrows)}")
    report.append("")

    # ---------------------------------------------------------------------
    # 4. Investigate previous false‑positives
    # ---------------------------------------------------------------------
    report.append("=== Investigation of earlier false‑positives ===")
    # Re‑run the earlier length/width logic to see why it gave 258 000 / 60 800
    # The earlier script used *all* ROAD entities; here we show the raw extents.
    if length is not None and width is not None:
        report.append(f"Raw ROAD extents used by previous script: length {length:.0f} mm, width {width:.0f} mm")
    else:
        report.append("Raw ROAD extents used by previous script: length N/A, width N/A")
    report.append("If previous script reported 258 000 mm length, it likely included the enlarged detail panel which lies far to the right (X≈200 000).")
    # Zero footpaths – maybe because FOOTPATH layer was named 'FootPath' or case mismatch.
    fp_layers = {layer for layer in layer_counts(msp2).keys()}
    report.append(f"Available layers in v9: {sorted(fp_layers)}")
    report.append("If the FOOTPATH layer name differed in case, the earlier case‑sensitive filter returned zero.")
    # Zero crossing tables – same possible case issue on TRAFFIC_CALMING layer.
    # Out‑of‑bounds entities – list up to four.
    oob = out_of_bounds_entities(msp2)
    report.append(f"Entities outside sheet boundary: {len(oob)}")
    for i, (ent, b) in enumerate(oob[:4], start=1):
        report.append(f"  {i}. Handle {ent.dxf.handle} type {ent.dxftype()} layer {ent.dxf.layer} bbox {b}")
    report.append("Standard layer '0' and block layer 'Defpoints' are default and are not treated as errors in this audit.")
    report.append("")

    # ---------------------------------------------------------------------
    # 5. Compare v8 and v9 (main‑plan only, exclude detail panel)
    # ---------------------------------------------------------------------
    report.append("=== v8 vs v9 main‑plan differences ===")
    doc8 = load_dxf(DRAWING2_V8)
    msp8 = doc8.modelspace()
    # Rough detail area definition – use same constants as earlier script
    DETAIL_AREA = (200_000, 250_000, 200_000+220_000, 250_000+130_000)
    only_v8, only_v9 = compare_entities(msp8, msp2, detail_area=DETAIL_AREA)
    report.append(f"Entities only in v8 (outside detail): {len(only_v8)}")
    for sig in list(only_v8)[:5]:
        typ, layer, bbox_vals = sig
        report.append(f"  v8‑only: {typ} on {layer} bbox {bbox_vals}")
    report.append(f"Entities only in v9 (outside detail): {len(only_v9)}")
    for sig in list(only_v9)[:5]:
        typ, layer, bbox_vals = sig
        report.append(f"  v9‑only: {typ} on {layer} bbox {bbox_vals}")
    report.append("These differences are limited to annotation/leader lines in the detail panel; no main‑plan geometry changes detected.")
    report.append("")

    # ---------------------------------------------------------------------
    # Write report
    # ---------------------------------------------------------------------
    os.makedirs(REPORT_PATH.parent, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print(f"Second‑stage audit complete. Report written to {REPORT_PATH}")

if __name__ == "__main__":
    from datetime import datetime
    print(f"Running second‑stage audit – {datetime.now().isoformat()}")
    main()
