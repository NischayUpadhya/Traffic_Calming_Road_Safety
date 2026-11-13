"""Visual inspection (text-only) for drawing 02 v9
Creates reports/cad_final_visual_inspection.txt and optionally a PNG preview if Matplotlib works.
"""
import os, sys
from pathlib import Path

# Try imports; if matplotlib unavailable, we skip preview.
try:
    import ezdxf
except Exception:
    print('ezdxf not installed – abort')
    sys.exit(1)

has_matplotlib = False
try:
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import MatplotlibBackend
    has_matplotlib = True
except Exception:
    has_matplotlib = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DRAWING = PROJECT_ROOT / "drawings" / "02_proposed_traffic_calming_road_v9.dxf"
REPORT = PROJECT_ROOT / "reports" / "cad_final_visual_inspection.txt"
PREVIEW = PROJECT_ROOT / "reports" / "cad_v9_preview.png"

def bbox(e):
    try:
        ext = e.bbox()
        return ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y
    except Exception:
        if e.dxftype() == "TEXT":
            h = e.dxf.height
            x, y = e.dxf.insert.x, e.dxf.insert.y
            return x - h/2, y - h/2, x + h/2, y + h/2
        return None

def fmt(e):
    h = e.dxf.handle
    typ = e.dxftype()
    layer = getattr(e.dxf, "layer", "<none>")
    b = bbox(e)
    return f"Handle {h}: {typ} on {layer}, bbox {b}"

def main():
    doc = ezdxf.readfile(str(DRAWING))
    msp = doc.modelspace()
    out = []
    # Task 1 crossing outlines
    out.append('=== Task 1 – Crossing outlines (handles 143, 153) ===')
    for h in ['143','153']:
        e = doc.entitydb.get(h)
        if e:
            out.append(fmt(e))
            out.append('PASS')
        else:
            out.append(f'Handle {h} not found – FAIL')
    out.append('')
    # Task 2 zebra lines groups
    groups = {
        'A': ['144','145','146','147','148','149','14A'],
        'B': ['154','155','156','157','158','159','15A']
    }
    for label, handles in groups.items():
        out.append(f'=== Task 2 – Zebra group {label} ===')
        for h in handles:
            e = doc.entitydb.get(h)
            if e:
                out.append(fmt(e))
            else:
                out.append(f'Handle {h} not found – FAIL')
        out.append('')
    # Task 3 zebra full‑width check
    road_ents = [e for e in msp if getattr(e.dxf,'layer','').upper()=='ROAD']
    ys=[]
    for e in road_ents:
        b=bbox(e)
        if b:
            ys.extend([b[1],b[3]])
    if ys:
        ymin, ymax = min(ys), max(ys)
        full=True
        for h in sum(groups.values(),[]):
            e=doc.entitydb.get(h)
            if e and e.dxftype()=='LINE':
                b=bbox(e)
                if not (abs(b[1]-ymin)<10 and abs(b[3]-ymax)<10):
                    full=False
        out.append(f'Zebra bar full‑width: {'PASS' if full else 'FAIL'}')
    else:
        out.append('Zebra bar full‑width: NOT VERIFIED (no ROAD extents)')
    out.append('')
    # Task 4 sheet boundary & four texts
    sheet=(0,0,420_000,297_000)
    out.append('=== Task 4 – Text entities (1BC,1BD,240,242) ===')
    for h in ['1BC','1BD','240','242']:
        e=doc.entitydb.get(h)
        if e:
            b=bbox(e)
            out_of = b[0]<sheet[0] or b[1]<sheet[1] or b[2]>sheet[2] or b[3]>sheet[3]
            out.append(f"{fmt(e)} – out_of_bounds={out_of}")
        else:
            out.append(f'Handle {h} not found – FAIL')
    out.append('')
    # Task 5 detail panel labels (X>200k)
    out.append('=== Task 5 – Detail‑panel labels (X>200k) ===')
    for e in msp:
        if e.dxftype() in {'TEXT','MTEXT'}:
            b=bbox(e)
            if b and b[0]>200_000:
                out_of = b[0]<sheet[0] or b[1]<sheet[1] or b[2]>sheet[2] or b[3]>sheet[3]
                out.append(f"Label {e.dxf.handle} at {b} – out_of_bounds={out_of}")
    out.append('')
    # Task 6 preview if possible
    if has_matplotlib:
        try:
            fig=plt.figure(figsize=(10,8))
            ax=fig.add_axes([0,0,1,1])
            MatplotlibBackend(msp).draw(ax)
            ax.set_aspect('equal')
            plt.title('Preview')
            plt.savefig(str(PREVIEW), dpi=150)
            out.append(f'Preview saved to {PREVIEW}')
        except Exception as exc:
            out.append(f'Preview generation failed: {exc}')
    else:
        out.append('Matplotlib not available – preview not generated')

    # write report
    os.makedirs(REPORT.parent, exist_ok=True)
    with open(REPORT,'w',encoding='utf-8') as f:
        f.write('\n'.join(out))
    print('Report written to',REPORT)
    # verify existence and sizes
    if REPORT.is_file():
        print('Report size:',REPORT.stat().st_size,'bytes')
    if PREVIEW.is_file():
        print('Preview size:',PREVIEW.stat().st_size,'bytes')

if __name__=='__main__':
    main()
