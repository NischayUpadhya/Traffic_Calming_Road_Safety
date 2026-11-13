import ezdxf, os, shutil, json

project_root = r"C:\final year\Traffic_Calming_Road_Safety"
drawings_dir = os.path.join(project_root, "drawings")
reports_dir = os.path.join(project_root, "reports")

v9_path = os.path.join(drawings_dir, "02_proposed_traffic_calming_road_v9.dxf")
v10_path = os.path.join(drawings_dir, "02_proposed_traffic_calming_road_v10.dxf")

# Ensure no existing v10
if os.path.exists(v10_path):
    os.remove(v10_path)
# Copy v9 to v10
shutil.copyfile(v9_path, v10_path)

doc = ezdxf.readfile(v10_path)
msp = doc.modelspace()
entitydb = doc.entitydb

def get_entity(handle):
    return entitydb.get(handle)

# Delete existing zebra line entities (handles 144-14A and 154-15A)
def handle_range(start, end):
    start_i = int(start, 16)
    end_i = int(end, 16)
    return [format(i, 'X').upper() for i in range(start_i, end_i+1)]

zebra_handles = set(handle_range('144','14A') + handle_range('154','15A'))
for h in zebra_handles:
    ent = get_entity(h)
    if ent:
        try:
            msp.delete_entity(ent)
        except Exception as e:
            print(f"Failed delete {h}: {e}")

# Add corrected vertical zebra bars inside crossing outlines (handles 143 and 153)
outline_handles = ['143','153']
zebra_layer = 'TRAFFIC_CALMING'  # use same layer as original
bar_width = 200  # mm
spacing = 300    # mm
offset = 200     # mm from outline edge
added_handles = []
for oh in outline_handles:
    outline = get_entity(oh)
    if not outline:
        print(f"Outline {oh} missing")
        continue
    # Get vertices of LWPOLYLINE
    pts = [pt[:2] for pt in outline.get_points('xy')]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    x = xmin + offset
    while x + bar_width <= xmax - offset:
        rect = [(x, ymin), (x+bar_width, ymin), (x+bar_width, ymax), (x, ymax)]
        bar = msp.add_lwpolyline(rect, dxfattribs={'layer': zebra_layer, 'closed': True})
        added_handles.append(bar.dxf.handle)
        x += bar_width + spacing

# Move out-of-bounds text (handles 1BC,1BD,240,242) inside sheet border (0,0,420000,297000)
# Simple approach: shift Y down so ymax <= 296000
sheet_max_y = 297000
shift_needed = 0
text_handles = ['1BC','1BD','240','242']
for th in text_handles:
    ent = get_entity(th)
    if not ent:
        continue
    # Determine bbox using entity's start/insert points (works for TEXT/MTEXT)
    if ent.dxftype() == 'TEXT' or ent.dxftype() == 'MTEXT':
        # Approximate using insert point and height
        insert = ent.dxf.insert
        height = getattr(ent.dxf, 'height', 0)
        ymax = insert.y + height/2
        if ymax > sheet_max_y:
            needed = ymax - sheet_max_y + 1000  # extra 1m margin
            shift_needed = max(shift_needed, needed)

if shift_needed > 0:
    for th in text_handles:
        ent = get_entity(th)
        if not ent:
            continue
        if hasattr(ent.dxf, 'insert'):
            ent.dxf.insert = (ent.dxf.insert.x, ent.dxf.insert.y - shift_needed, ent.dxf.insert.z)

# Save DXF
doc.saveas(v10_path)

# Write change log
change_log_path = os.path.join(reports_dir, 'cad_v10_change_log.txt')
with open(change_log_path, 'w') as f:
    f.write('CAD V10 Change Log\n')
    f.write('===================\n')
    f.write('Removed original zebra line handles:\n')
    for h in sorted(zebra_handles):
        f.write(f'  - {h}\n')
    f.write('\nAdded vertical zebra bar handles (LWPOLYLINE):\n')
    for h in added_handles:
        f.write(f'  - {h}\n')
    f.write('\nMoved out-of-bounds text entities down by {:.0f} mm.\n'.format(shift_needed))
    f.write('Affected text handles: {}\n'.format(', '.join(text_handles)))
    f.write('\nAssumptions: bar_width=200mm, spacing=300mm, offset=200mm, layer=TRAFFIC_CALMING.\n')

print('V10 creation complete')
