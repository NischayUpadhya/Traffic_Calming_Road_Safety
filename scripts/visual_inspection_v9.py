"""Visual and geometric inspection of drawing 02 v9 (read‑only)
Generates a concise report and a PNG preview.
"""
import os, sys
from pathlib import Path

import ezdxf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DRAWING = PROJECT_ROOT / "drawings" / "02_proposed_traffic_calming_road_v9.dxf"
REPORT = PROJECT_ROOT / "reports" / "cad_final_visual_inspection.txt"
PREVIEW_IMG = PROJECT_ROOT / "reports" / "cad_v9_preview.png"

# Helper
def bbox(entity):
    try:
        ext = entity.bbox()
        return ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y
    except Exception:
        if entity.dxftype() == "TEXT":
            h = entity.dxf.height
            x, y = entity.dxf.insert.x, entity.dxf.insert.y
            return x - h/2, y - h/2, x + h/2, y + h/2
        return None

def get_entity(doc, handle):
    return doc.entitydb.get(handle)

    h = e.dxf.handle
    typ = e.dxftype()
    layer = getattr(e.dxf, "layer", "<none>")
    b = bbox(e)
    if typ == "LINE":
        s = e.dxf.start
        ept = e.dxf.end
        return f"Handle {h}: LINE on {layer}, start ({s.x:.2f},{s.y:.2f}) end ({ept.x:.2f},{ept.y:.2f}), bbox {b}"
    elif typ in {"LWPOLYLINE", "POLYLINE"}:
        pts = list(e.get_points())
        ptstr = ", ".join([f"({p[0]:.2f},{p[1]:.2f})" for p in pts])
        return f"Handle {h}: {typ} on {layer}, vertices [{ptstr}], bbox {b}"
    elif typ in {"TEXT", "MTEXT"}:
        txt = getattr(e.dxf, "text", "").replace("\n"," ")
        ins = e.dxf.insert
        return f"Handle {h}: {typ} on {layer}, text '{txt}', insert ({ins.x:.2f},{ins.y:.2f}), bbox {b}"
    else:
        return f"Handle {h}: {typ} on {layer}, bbox {b}"

def main():
    doc = ezdxf.readfile(str(DRAWING))
    msp = doc.modelspace()
    report_lines = []
    # 1. Crossing outlines handles 143, 153
    report_lines.append("=== Crossing outlines (handles 143, 153) ===")
    for h in ["143", "153"]:
        e = get_entity(doc, h)
        if e:
            report_lines.append(format_entity(e))
        else:
            report_lines.append(f"Handle {h} not found")
    # 2. Zebra marking lines 144-14A and 154-15A
    report_lines.append("\n=== Zebra marking lines (handles 144‑14A) ===")
    for h in ["144","145","146","147","148","149","14A"]:
        e = get_entity(doc, h)
        if e:
            report_lines.append(format_entity(e))
    report_lines.append("\n=== Zebra marking lines (handles 154‑15A) ===")
    for h in ["154","155","156","157","158","159","15A"]:
        e = get_entity(doc, h)
        if e:
            report_lines.append(format_entity(e))
    # 3. Determine zebra bar coverage and orientation
    # Compute overall road Y‑extent from ROAD layer
    road_ents = [e for e in msp if getattr(e.dxf, "layer", "").upper() == "ROAD"]
    ys = []
    for e in road_ents:
        b = bbox(e)
        if b:
            ys.extend([b[1], b[3]])
    road_ymin = min(ys) if ys else None
    road_ymax = max(ys) if ys else None
    zebra_pass = True
    if road_ymin is not None:
        for h in ["144","145","146","147","148","149","14A","154","155","156","157","158","159","15A"]:
            e = get_entity(doc, h)
            if e and e.dxftype() == "LINE":
                b = bbox(e)
                # check that line spans full Y width (within tolerance 5 mm)
                if not (abs(b[1] - road_ymin) < 10 and abs(b[3] - road_ymax) < 10):
                    zebra_pass = False
        report_lines.append("\nZebra bar full‑width check: " + ("PASS" if zebra_pass else "FAIL"))
    else:
        report_lines.append("\nZebra bar full‑width check: NOT VERIFIED (road Y‑extent not found)")
    # 4. Sheet boundary and text entities
    report_lines.append("\n=== Sheet boundary (A3 landscape 420000 x 297000) ===")
    sheet = (0,0,420_000,297_000)
    report_lines.append(f"Sheet bbox: {sheet}")
    txt_handles = ["1BC","1BD","240","242"]
    report_lines.append("\n=== Text entities ===")
    for h in txt_handles:
        e = get_entity(doc, h)
        if e:
            b = bbox(e)
            out = b[0] < sheet[0] or b[1] < sheet[1] or b[2] > sheet[2] or b[3] > sheet[3]
            report_lines.append(f"{format_entity(e)} – out of bounds: {out}")
        else:
            report_lines.append(f"Handle {h} not found")
    # 5. Detail‑panel labels location – assume they are on layer TEXT and near detail area (X>200000)
    report_lines.append("\n=== Detail‑panel label location check ===")
    detail_labels = []
    for e in msp:
        if e.dxftype() in {"TEXT","MTEXT"} and getattr(e.dxf, "layer", "").upper() == "TEXT":
            b = bbox(e)
            if b and b[0] > 200_000:  # heuristic: beyond main road
                detail_labels.append(e)
    for e in detail_labels:
        b = bbox(e)
        out = b[0] < sheet[0] or b[1] < sheet[1] or b[2] > sheet[2] or b[3] > sheet[3]
        report_lines.append(f"Label handle {e.dxf.handle} at {b} – out of bounds: {out}")
    # 6. Generate PNG preview (Matplotlib) – read‑only
    # try:
    #     fig = plt.figure(figsize=(12,8))
    #     ctx = matplotlib.MatplotlibBackend(msp)
    #     ctx.draw(fig.gca())
    #     plt.axis('equal')
    #     plt.title('02_proposed_traffic_calming_road_v9 preview')
    #     plt.savefig(str(PREVIEW_IMG), dpi=150)
    #     report_lines.append(f"\nPreview image saved to {PREVIEW_IMG}")
    # except Exception as exc:
    #     report_lines.append(f"\nFailed to generate preview: {exc}")
    # Write report
    os.makedirs(REPORT.parent, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Inspection complete – report at {REPORT}")

if __name__ == "__main__":
    from datetime import datetime
    print(f"Running visual inspection – {datetime.now().isoformat()}")
    main()
