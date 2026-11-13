"""Visual inspection of drawing 02 v9 (read‑only)
Generates a concise report and a PNG preview.
"""
import os, sys
from pathlib import Path

try:
    import ezdxf
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import MatplotlibBackend
except Exception:
    print("Required packages missing – install ezdxf and matplotlib.")
    sys.exit(1)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DRAWING = PROJECT_ROOT / "drawings" / "02_proposed_traffic_calming_road_v9.dxf"
REPORT = PROJECT_ROOT / "reports" / "cad_final_visual_inspection.txt"
PREVIEW_IMG = PROJECT_ROOT / "reports" / "cad_v9_preview.png"

# ---------------------------------------------------------------------------
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
        return None

def format_entity(e):
    h = e.dxf.handle
    typ = e.dxftype()
    layer = getattr(e.dxf, "layer", "<none>")
    b = bbox(e)
    if typ == "LINE":
        s = e.dxf.start
        ept = e.dxf.end
        return f"Handle {h}: LINE on {layer}, start ({s.x:.2f},{s.y:.2f}) end ({ept.x:.2f},{ept.y:.2f}), bbox {b}"
    if typ in {"LWPOLYLINE", "POLYLINE"}:
        pts = list(e.get_points())
        ptstr = ", ".join([f"({p[0]:.2f},{p[1]:.2f})" for p in pts])
        return f"Handle {h}: {typ} on {layer}, vertices [{ptstr}], bbox {b}"
    if typ in {"TEXT", "MTEXT"}:
        txt = getattr(e.dxf, "text", "").replace("\n", " ")
        ins = e.dxf.insert
        return f"Handle {h}: {typ} on {layer}, text '{txt}', insert ({ins.x:.2f},{ins.y:.2f}), bbox {b}"
    return f"Handle {h}: {typ} on {layer}, bbox {b}"

def get_entity(doc, handle):
    return doc.entitydb.get(handle)

def main():
    doc = ezdxf.readfile(str(DRAWING))
    msp = doc.modelspace()
    report_lines = []

    # Task 1 – crossing outlines (handles 143, 153)
    report_lines.append("=== Task 1 – Crossing outlines (handles 143, 153) ===")
    for h in ["143", "153"]:
        e = get_entity(doc, h)
        if e:
            report_lines.append(format_entity(e))
            report_lines.append("PASS – outline entity found")
        else:
            report_lines.append(f"Handle {h} not found – FAIL")
    report_lines.append("")

    # Task 2 – Zebra marking lines (144–14A and 154–15A)
    zebra_groups = [("A", ["144","145","146","147","148","149","14A"]),
                    ("B", ["154","155","156","157","158","159","15A"])]
    for label, handles in zebra_groups:
        report_lines.append(f"=== Task 2 – Zebra group {label} lines ===")
        for h in handles:
            e = get_entity(doc, h)
            if e:
                report_lines.append(format_entity(e))
            else:
                report_lines.append(f"Handle {h} not found – FAIL")
        report_lines.append("")

    # Task 3 – zebra bar coverage & orientation
    # Determine road Y‑extent from ROAD layer
    road_ents = [e for e in msp if getattr(e.dxf, "layer", "").upper() == "ROAD"]
    ys = []
    for e in road_ents:
        b = bbox(e)
        if b:
            ys.extend([b[1], b[3]])
    road_ymin = min(ys) if ys else None
    road_ymax = max(ys) if ys else None
    zebra_full = True
    if road_ymin is not None:
        for _, handles in zebra_groups:
            for h in handles:
                e = get_entity(doc, h)
                if e and e.dxftype() == "LINE":
                    b = bbox(e)
                    # line should span roughly the full road width (tolerance 10 mm)
                    if not (abs(b[1] - road_ymin) < 10 and abs(b[3] - road_ymax) < 10):
                        zebra_full = False
        report_lines.append(f"Zebra bar full‑width check: {'PASS' if zebra_full else 'FAIL'}")
    else:
        report_lines.append("Zebra bar full‑width check: NOT VERIFIED (road Y‑extent not found)")
    report_lines.append("")

    # Task 4 – Sheet boundary and four text entities
    sheet = (0, 0, 420_000, 297_000)
    report_lines.append("=== Task 4 – Sheet boundary & text entities ===")
    report_lines.append(f"Sheet bbox: {sheet}")
    txt_handles = ["1BC", "1BD", "240", "242"]
    for h in txt_handles:
        e = get_entity(doc, h)
        if e:
            b = bbox(e)
            out = b[0] < sheet[0] or b[1] < sheet[1] or b[2] > sheet[2] or b[3] > sheet[3]
            report_lines.append(f"{format_entity(e)} – out‑of‑bounds: {out}")
        else:
            report_lines.append(f"Handle {h} not found – FAIL")
    report_lines.append("")

    # Task 5 – Detail‑panel labels location
    report_lines.append("=== Task 5 – Detail‑panel label location ===")
    # Heuristic: any TEXT entity with X > 200_000 belongs to detail panel
    for e in msp:
        if e.dxftype() in {"TEXT", "MTEXT"}:
            b = bbox(e)
            if b and b[0] > 200_000:
                out = b[0] < sheet[0] or b[1] < sheet[1] or b[2] > sheet[2] or b[3] > sheet[3]
                report_lines.append(f"Label handle {e.dxf.handle} at {b} – out‑of‑bounds: {out}")
    report_lines.append("")

    # Task 6 – generate PNG preview (read‑only)
    try:
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_axes([0, 0, 1, 1])
        ctx = MatplotlibBackend(msp)
        ctx.draw(ax)
        ax.set_aspect('equal')
        plt.title('02_proposed_traffic_calming_road_v9 preview')
        plt.savefig(str(PREVIEW_IMG), dpi=150)
        report_lines.append(f"Preview image saved to {PREVIEW_IMG}")
    except Exception as exc:
        report_lines.append(f"Preview generation failed: {exc}")

    # Write report
    os.makedirs(REPORT.parent, exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"Inspection complete – report at {REPORT}")

if __name__ == "__main__":
    from datetime import datetime
    print(f"Running visual inspection – {datetime.now().isoformat()}")
    main()
