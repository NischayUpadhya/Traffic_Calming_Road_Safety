import ezdxf, os, shutil, json, math

# Paths
project_root = r"C:\final year\Traffic_Calming_Road_Safety"
v9_path = os.path.join(project_root, "drawings", "02_proposed_traffic_calming_road_v9.dxf")
v10_path = os.path.join(project_root, "drawings", "02_proposed_traffic_calming_road_v10.dxf")
reports_dir = os.path.join(project_root, "reports")

# Ensure we don't overwrite existing v10
if os.path.exists(v10_path):
    raise FileExistsError(f"Target v10 file already exists: {v10_path}")

# Copy v9 to v10
shutil.copyfile(v9_path, v10_path)

# Load the DXF
doc = ezdxf.readfile(v10_path)
msp = doc.modelspace()
entitydb = doc.entitydb

def get_entity(handle):
    return entitydb.get(handle)

# Zebra line handles (hex ranges inclusive)
def handle_range(start_hex, end_hex):
    start = int(start_hex, 16)
    end = int(end_hex, 16)
    return [format(i, 'X').upper() for i in range(start, end + 1)]

zebra_handles = set(handle_range('144', '14A') + handle_range('154', '15A'))

# Delete existing zebra line entities (ignore missing)
for handle in zebra_handles:
    ent = get_entity(handle)
    if ent is not None:
        try:
            msp.delete_entity(ent)
        except Exception as e:
            print(f"Failed to delete entity {handle}: {e}")

# Crossing outline handles
outline_handles = ['143', '153']
# Use a deterministic layer for new zebra bars
zebra_layer = 'TRAFFIC_CALMING'

# Parameters for zebra bars (in mm)
bar_width = 200   # width of each bar
spacing = 300     # space between bars
offset = 200      # offset from outline edge inside

added_bars = []
for outline_handle in outline_handles:
    outline = get_entity(outline_handle)
    if outline is None:
        print(f"Outline handle {outline_handle} not found, skipping.")
        continue
    # Determine bounding box of outline
    try:
        # Most outlines are LWPOLYLINE rectangles
        points = []
        if outline.dxftype() == 'LWPOLYLINE':
            points = [pt[:2] for pt in outline.get_points('xy')]
        elif outline.dxftype() == 'POLYLINE':
            points = [(v.dxf.x, v.dxf.y) for v in outline.vertices()]
        else:
            # Fallback: try generic bbox method
            bbox = outline.bbox()
            points = [(bbox.extmin.x, bbox.extmin.y), (bbox.extmax.x, bbox.extmax.y)]
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
    except Exception as e:
        print(f"Failed to compute bbox for outline {outline_handle}: {e}")
        continue
    # Generate vertical bars within the outline
    x = xmin + offset
    while x + bar_width <= xmax - offset:
        # rectangle points (closed LWPOLYLINE)
        rect_pts = [
            (x, ymin),
            (x + bar_width, ymin),
            (x + bar_width, ymax),
            (x, ymax),
        ]
        bar = msp.add_lwpolyline(rect_pts, dxfattribs={'layer': zebra_layer, 'closed': True})
        added_bars.append(bar.dxf.handle)
        x += bar_width + spacing

# Save the modified DXF
doc.saveas(v10_path)

# Write change log
change_log_path = os.path.join(reports_dir, 'cad_v10_change_log.txt')
with open(change_log_path, 'w') as f:
    f.write('CAD V10 Change Log\n')
    f.write('===================\n')
    f.write('Removed zebra line handles (original incorrect orientation):\n')
    for h in sorted(zebra_handles):
        f.write(f'  - {h}\n')
    f.write('\nAdded vertical zebra bar handles (LWPOLYLINE):\n')
    for h in added_bars:
        f.write(f'  - {h}\n')
    f.write('\nAssumptions and parameters used:\n')
    f.write(f'Bar width: {bar_width} mm, spacing: {spacing} mm, offset from outline edge: {offset} mm\n')
    f.write(f'Layer for zebra bars: {zebra_layer}\n')

print('V10 DXF creation and change log completed.')
