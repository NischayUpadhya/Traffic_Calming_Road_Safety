import ezdxf, os, shutil, json, math

# Paths
v9_path = r"C:\final year\Traffic_Calming_Road_Safety\drawings\02_proposed_traffic_calming_road_v9.dxf"
v10_path = r"C:\final year\Traffic_Calming_Road_Safety\drawings\02_proposed_traffic_calming_road_v10.dxf"
reports_dir = r"C:\final year\Traffic_Calam\reports"  # placeholder, will adjust later

# Ensure we don't overwrite existing v10
if os.path.exists(v10_path):
    raise FileExistsError(f"Target v10 file already exists: {v10_path}")

# Copy v9 to v10
shutil.copyfile(v9_path, v10_path)

# Load the DXF
doc = ezdxf.readfile(v10_path)
msp = doc.modelspace()

# Helper to get entity by handle
entitydb = doc.entitydb

def get_entity(handle):
    return entitydb.get(handle)

# Identify zebra line handles (hex ranges)
# Helper to generate handle strings in range inclusive
def handle_range(start_hex, end_hex):
    start = int(start_hex, 16)
    end = int(end_hex, 16)
    return [format(i, 'X').upper() for i in range(start, end + 1)]

zebra_handles = set(handle_range('144', '14A') + handle_range('154', '15A'))
# Delete existing zebra line entities
for handle in list(zebra_handles):
    ent = get_entity(handle)
    if ent is not None:
        try:
            msp.delete_entity(ent)
        except Exception as e:
            print(f"Failed to delete entity {handle}: {e}")

# Get crossing outlines to compute extents and layer for zebra bars
cross_outline_handles = ['143', '153']
# Assume zebra bars should be on same layer as original zebra lines (if any remain), otherwise 'TRAFFIC_CALMING'
zebra_layer = 'TRAFFIC_CALMING'
# Try to fetch layer from a zebra line that still exists (maybe none); fallback to above.
for h in ['144', '154']:
    ent = get_entity(h)
    if ent is not None:
        zebra_layer = ent.dxf.layer
        break

# Parameters for zebra bars
bar_width = 200  # mm
spacing = 300    # mm
offset_from_edge = 200  # mm inside outline

added_bars = []
for outline_handle in cross_outline_handles:
    outline = get_entity(outline_handle)
    if outline is None:
        print(f"Outline handle {outline_handle} not found")
        continue
    # Assuming outline is a LWPOLYLINE rectangle; get its extents
    # Use DXF bounding box via ezdxf's geometric utilities
    try:
        bbox = outline.bbox()
        xmin, ymin, xmax, ymax = bbox.extmin.x, bbox.extmin.y, bbox.extmax.x, bbox.extmax.y
    except Exception as e:
        print(f"Failed to get bbox for outline {outline_handle}: {e}")
        continue
    # Carriageway Y range (should be same as ymin..ymax)
    y_bottom = ymin
    y_top = ymax
    # Start X after offset
    x = xmin + offset_from_edge
    while x + bar_width <= xmax - offset_from_edge:
        # Create rectangle polyline for bar
        points = [
            (x, y_bottom),
            (x + bar_width, y_bottom),
            (x + bar_width, y_top),
            (x, y_top),
        ]
        lwpoly = msp.add_lwpolyline(points, dxfattribs={'layer': zebra_layer, 'closed': True})
        added_bars.append(lwpoly.dxf.handle)
        x += bar_width + spacing

# Save changes
doc.saveas(v10_path)

# Write change log
log_path = os.path.join(os.path.dirname(v10_path), '..', 'reports', 'cad_v10_change_log.txt')
log_path = os.path.abspath(log_path)
with open(log_path, 'w') as f:
    f.write('CAD V10 Change Log\n')
    f.write('===================\n')
    f.write('Removed zebra line handles:\n')
    for h in sorted(zebra_handles):
        f.write(f'  - {h}\n')
    f.write('\nAdded vertical zebra bar handles (LWPOLYLINE):\n')
    for h in added_bars:
        f.write(f'  - {h}\n')
    f.write('\nAssumptions:\n')
    f.write(f'Bar width: {bar_width} mm, spacing: {spacing} mm, offset from outline edge: {offset_from_edge} mm.\n')
    f.write('Layer used: ' + zebra_layer + '\n')

print('V10 creation complete')
