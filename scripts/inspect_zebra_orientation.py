"""Read‑only inspection of zebra‑crossing orientation in v9 drawing.
Creates reports/cad_zebra_orientation_review.txt.
"""
import os, sys
from pathlib import Path

try:
    import ezdxf
except Exception:
    print('ezdxf not installed')
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DRAWING = PROJECT_ROOT / 'drawings' / '02_proposed_traffic_calming_road_v9.dxf'
REPORT = PROJECT_ROOT / 'reports' / 'cad_zebra_orientation_review.txt'

# Helper to get bbox
def bbox(e):
    try:
        ext = e.bbox()
        return ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y
    except Exception:
        if e.dxftype() == 'TEXT':
            h = e.dxf.height
            x, y = e.dxf.insert.x, e.dxf.insert.y
            return x - h/2, y - h/2, x + h/2, y + h/2
        return None

def fmt_entity(e):
    h = e.dxf.handle
    typ = e.dxftype()
    layer = getattr(e.dxf, 'layer', '<none>')
    b = bbox(e)
    if typ == 'LINE':
        s = e.dxf.start
        ept = e.dxf.end
        return f"Handle {h}: LINE on {layer}, start ({s.x:.0f},{s.y:.0f}) end ({ept.x:.0f},{ept.y:.0f}), bbox {b}"
    elif typ in {'LWPOLYLINE','POLYLINE'}:
        pts = list(e.get_points())
        ptstr = ', '.join([f'({p[0]:.0f},{p[1]:.0f})' for p in pts])
        return f"Handle {h}: {typ} on {layer}, vertices [{ptstr}], bbox {b}"
    elif typ in {'TEXT','MTEXT'}:
        txt = getattr(e.dxf, 'text', '').replace('\n',' ')
        ins = e.dxf.insert
        return f"Handle {h}: {typ} on {layer}, text '{txt}', insert ({ins.x:.0f},{ins.y:.0f}), bbox {b}"
    else:
        return f"Handle {h}: {typ} on {layer}, bbox {b}"

def main():
    doc = ezdxf.readfile(str(DRAWING))
    msp = doc.modelspace()
    lines = []
    # Crossing outlines handles 143 and 153
    for h in ['143','153']:
        e = doc.entitydb.get(h)
        if e:
            lines.append(fmt_entity(e))
        else:
            lines.append(f'Handle {h} NOT FOUND')
    # Zebra lines groups
    zebra_a = ['144','145','146','147','148','149','14A']
    zebra_b = ['154','155','156','157','158','159','15A']
    zebra_details = []
    for h in zebra_a + zebra_b:
        e = doc.entitydb.get(h)
        if e:
            zebra_details.append(fmt_entity(e))
        else:
            zebra_details.append(f'Handle {h} NOT FOUND')
    # Text handles
    text_handles = ['1BC','1BD','240','242']
    text_details = []
    for h in text_handles:
        e = doc.entitydb.get(h)
        if e:
            text_details.append(fmt_entity(e))
        else:
            text_details.append(f'Handle {h} NOT FOUND')
    # Sheet border (A3 landscape 420000 x 297000)
    sheet_bbox = (0,0,420_000,297_000)
    # Determine if any text is out of bounds
    out_bounds = []
    for h in text_handles:
        e = doc.entitydb.get(h)
        if e:
            b = bbox(e)
            out = b[0] < sheet_bbox[0] or b[1] < sheet_bbox[1] or b[2] > sheet_bbox[2] or b[3] > sheet_bbox[3]
            out_bounds.append((h, out, b))
    # Build report
    report_lines = []
    report_lines.append('--- CAD Zebra Orientation Review (read‑only) ---')
    report_lines.append('')
    report_lines.append('1. Crossing outlines')
    report_lines.extend(lines)
    report_lines.append('')
    report_lines.append('2. Zebra marking lines (group A then B)')
    report_lines.extend(zebra_details)
    report_lines.append('')
    report_lines.append('3. Sheet border (A3 landscape)')
    report_lines.append(f'Sheet bounding box: {sheet_bbox}')
    report_lines.append('')
    report_lines.append('4. Text entities and out‑of‑bounds check')
    for h, out, b in out_bounds:
        report_lines.append(f'Handle {h}: bbox {b}, out_of_bounds = {out}')
    report_lines.append('')
    # Proposed correct zebra orientation description
    report_lines.append('5. Proposed correct zebra‑bar arrangement')
    report_lines.append('   - Road runs along X (increasing X direction).')
    report_lines.append('   - Carriageway occupies Y from approx 182000 to 189000 (width 7000 mm).')
    report_lines.append('   - Existing zebra lines run horizontally (constant Y), which is parallel to the road.')
    report_lines.append('   - Correct zebra bars should be vertical, i.e., lines with constant X and varying Y')
    report_lines.append('   - Each bar should span the full carriageway Y range (≈182000‑189000)')
    report_lines.append('   - Bars should be spaced regularly along X within the crossing area (e.g., every 200‑300 mm)')
    report_lines.append('   - For crossing at X≈127000‑133000, typical bars could be at X = 128000, 128300, 128600, … up to 132700')
    report_lines.append('   - Similarly for crossing at X≈207000‑213000, bars at X = 208000, 208300, … up to 212700')
    report_lines.append('')
    report_lines.append('NOTE: No DXF modifications have been made. This is a read‑only analysis.')

    os.makedirs(REPORT.parent, exist_ok=True)
    with open(REPORT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    print('Inspection report written to', REPORT)
    # verify existence
    if REPORT.is_file():
        print('Report size bytes:', REPORT.stat().st_size)

if __name__ == '__main__':
    main()
