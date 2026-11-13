"""
=============================================================================
  create_existing_road.py
  BCV755A Road Safety Engineering – Final Year Project
  Title : Design of an Integrated Traffic Calming System for Accident
          Prevention on Urban Roads Using CAD
  Drawing: 01_existing_urban_road.dxf  –  Existing Urban Road Corridor
  Author : Final Year Engineering Student
  Units  : MILLIMETRES  (all geometry at 1:1 scale)
  Layers : ROAD | LANE_MARKINGS | FOOTPATH | DIMENSIONS | TEXT | TITLE_BLOCK
=============================================================================
  Install dependency (if missing):
      pip install ezdxf
=============================================================================
"""

# ---------------------------------------------------------------------------
# 0. Imports
# ---------------------------------------------------------------------------
import os
import sys

# Check for ezdxf; print install command if absent
try:
    import ezdxf
    from ezdxf import colors
    from ezdxf.enums import TextEntityAlignment
except ModuleNotFoundError:
    print("ezdxf is not installed.  Run:  pip install ezdxf")
    sys.exit(1)

# Load standard CAD linetypes (DASHED, CENTER, etc.) into every new document
import ezdxf as _ezdxf

# ---------------------------------------------------------------------------
# 1. Geometry constants  (all in millimetres)
# ---------------------------------------------------------------------------
ROAD_LENGTH       = 200_000   # 200 m  – corridor length (X-axis)
CARRIAGEWAY_W     =   7_000   # 7 m   – two-way carriageway
LANE_W            =   3_500   # 3.5 m – single lane width
FOOTPATH_W        =   2_000   # 2 m   – footpath each side
TOTAL_CORRIDOR_W  =  11_000   # 11 m  – full corridor  (footpath + road + footpath)

# Origin: bottom-left of the lower footpath
X0, Y0 = 10_000, 10_000       # leave margin from origin

# Key Y-coordinates
Y_BOTTOM_FOOTPATH  = Y0
Y_LOWER_KERB       = Y0 + FOOTPATH_W                        # 2 000 mm above Y0
Y_LANE_DIVIDER     = Y_LOWER_KERB + LANE_W                  # 5 500 mm above Y0
Y_CENTRELINE       = Y_LOWER_KERB + CARRIAGEWAY_W / 2       # 5 500 mm (same as divider = centre)
Y_UPPER_KERB       = Y_LOWER_KERB + CARRIAGEWAY_W           # 9 000 mm above Y0
Y_TOP_FOOTPATH     = Y0 + TOTAL_CORRIDOR_W                  # 11 000 mm above Y0

X_END = X0 + ROAD_LENGTH   # right end of the corridor

# ---------------------------------------------------------------------------
# 2. DXF document setup
# ---------------------------------------------------------------------------
doc = ezdxf.new(dxfversion="R2010")
doc.header["$INSUNITS"] = 4            # 4 = millimetres
doc.header["$LUNITS"]   = 2            # decimal
doc.header["$LUPREC"]   = 0            # 0 decimal places for linear

# Load standard linetypes so DASHED / CENTER / CONTINUOUS are available
ezdxf.setup_linetypes(doc)

msp = doc.modelspace()

# ---------------------------------------------------------------------------
# 3. Layer definitions
# ---------------------------------------------------------------------------
LAYER_ROAD        = "ROAD"
LAYER_LANE        = "LANE_MARKINGS"
LAYER_FOOTPATH    = "FOOTPATH"
LAYER_DIM         = "DIMENSIONS"
LAYER_TEXT        = "TEXT"
LAYER_TITLEBLOCK  = "TITLE_BLOCK"

layer_defs = [
    # (name,          ACI-colour, linetype)
    (LAYER_ROAD,       colors.CYAN,    "CONTINUOUS"),
    (LAYER_LANE,       colors.YELLOW,  "CENTER"),
    (LAYER_FOOTPATH,   7,              "CONTINUOUS"),   # 7 = white/black
    (LAYER_DIM,        colors.RED,     "CONTINUOUS"),
    (LAYER_TEXT,       colors.WHITE,   "CONTINUOUS"),
    (LAYER_TITLEBLOCK, colors.BLUE,    "CONTINUOUS"),
]

for lname, lcol, llt in layer_defs:
    if doc.layers.has_entry(lname):
        doc.layers.get(lname).dxf.color   = lcol
        doc.layers.get(lname).dxf.linetype = llt
    else:
        doc.layers.add(lname, dxfattribs={"color": lcol, "linetype": llt})

# ---------------------------------------------------------------------------
# 4. Helper functions
# ---------------------------------------------------------------------------

def add_line(layer, start, end, ltype_override=None):
    """Add a LINE entity to modelspace."""
    attribs = {"layer": layer}
    if ltype_override:
        attribs["linetype"] = ltype_override
    msp.add_line(start, end, dxfattribs=attribs)


def add_text(layer, text, insert, height=400, rotation=0, halign="LEFT"):
    """Add a simple TEXT entity."""
    align_map = {
        "LEFT":   TextEntityAlignment.LEFT,
        "CENTER": TextEntityAlignment.CENTER,
        "RIGHT":  TextEntityAlignment.RIGHT,
        "MIDDLE": TextEntityAlignment.MIDDLE_CENTER,
    }
    t = msp.add_text(
        text,
        height=height,
        rotation=rotation,
        dxfattribs={"layer": layer},
    )
    t.set_placement(insert, align=align_map.get(halign, TextEntityAlignment.LEFT))


def add_mtext_block(layer, text, insert, char_height=350, width=0):
    """Add an MTEXT entity (supports multi-line \\P)."""
    attribs = {
        "layer":       layer,
        "insert":      insert,
        "char_height": char_height,
        "width":       width,
    }
    msp.add_mtext(text, dxfattribs=attribs)


def hline(layer, x1, x2, y, ltype=None):
    """Horizontal line shorthand."""
    add_line(layer, (x1, y), (x2, y), ltype)


def vline(layer, x, y1, y2, ltype=None):
    """Vertical line shorthand."""
    add_line(layer, (x, y1), (x, y2), ltype)


# ---------------------------------------------------------------------------
# 5. ROAD boundaries  (ROAD layer)
# ---------------------------------------------------------------------------
# Outer corridor rectangle  (bottom edge + top edge + left + right verticals)
# Bottom outer edge of corridor
hline(LAYER_ROAD, X0, X_END, Y_BOTTOM_FOOTPATH)
# Top outer edge of corridor
hline(LAYER_ROAD, X0, X_END, Y_TOP_FOOTPATH)
# Left boundary
vline(LAYER_ROAD, X0,    Y_BOTTOM_FOOTPATH, Y_TOP_FOOTPATH)
# Right boundary
vline(LAYER_ROAD, X_END, Y_BOTTOM_FOOTPATH, Y_TOP_FOOTPATH)

# Lower kerb  (carriageway / footpath boundary at bottom)
hline(LAYER_ROAD, X0, X_END, Y_LOWER_KERB)
# Upper kerb  (carriageway / footpath boundary at top)
hline(LAYER_ROAD, X0, X_END, Y_UPPER_KERB)

# ---------------------------------------------------------------------------
# 6. FOOTPATH hatching indicator lines  (FOOTPATH layer, dashed)
# ---------------------------------------------------------------------------
# Draw several short diagonal hatch lines inside the lower footpath strip
HATCH_SPACING = 5_000  # mm between hatch lines
for xi in range(X0, X_END, HATCH_SPACING):
    # Lower footpath hatch
    msp.add_line(
        (xi, Y_BOTTOM_FOOTPATH),
        (xi + FOOTPATH_W, Y_LOWER_KERB),
        dxfattribs={"layer": LAYER_FOOTPATH, "linetype": "CONTINUOUS"},
    )
    # Upper footpath hatch
    msp.add_line(
        (xi, Y_UPPER_KERB),
        (xi + FOOTPATH_W, Y_TOP_FOOTPATH),
        dxfattribs={"layer": LAYER_FOOTPATH, "linetype": "CONTINUOUS"},
    )

# Footpath boundary lines (thicker representation using the FOOTPATH layer)
hline(LAYER_FOOTPATH, X0, X_END, Y_BOTTOM_FOOTPATH)
hline(LAYER_FOOTPATH, X0, X_END, Y_TOP_FOOTPATH)

# ---------------------------------------------------------------------------
# 7. LANE MARKINGS  (LANE_MARKINGS layer)
# ---------------------------------------------------------------------------
# Centre-line (runs along the mid of the carriageway; same as lane divider
# for a 2-lane road with one line)
hline(LAYER_LANE, X0, X_END, Y_LANE_DIVIDER, "DASHED")

# Lane direction arrows (every 20 m)  – drawn with simple polyline arrowheads
ARROW_SPACING  = 20_000   # mm
ARROW_LEN      = 3_000    # arrow shaft length  (mm)
ARROW_HEAD_LEN = 1_000
ARROW_HEAD_W   = 500

for xi in range(int(X0 + 10_000), int(X_END - 10_000), ARROW_SPACING):
    # Southbound lane (below centreline) → arrow pointing LEFT (negative X)
    sb_y = Y_LOWER_KERB + LANE_W / 2   # mid of south lane
    shaft_start = (xi + ARROW_LEN / 2, sb_y)
    shaft_end   = (xi - ARROW_LEN / 2, sb_y)
    add_line(LAYER_LANE, shaft_start, shaft_end)
    # arrowhead
    add_line(LAYER_LANE, shaft_end,
             (shaft_end[0] + ARROW_HEAD_LEN, sb_y + ARROW_HEAD_W))
    add_line(LAYER_LANE, shaft_end,
             (shaft_end[0] + ARROW_HEAD_LEN, sb_y - ARROW_HEAD_W))

    # Northbound lane (above centreline) → arrow pointing RIGHT (positive X)
    nb_y = Y_LANE_DIVIDER + LANE_W / 2   # mid of north lane
    shaft_start2 = (xi - ARROW_LEN / 2, nb_y)
    shaft_end2   = (xi + ARROW_LEN / 2, nb_y)
    add_line(LAYER_LANE, shaft_start2, shaft_end2)
    # arrowhead
    add_line(LAYER_LANE, shaft_end2,
             (shaft_end2[0] - ARROW_HEAD_LEN, nb_y + ARROW_HEAD_W))
    add_line(LAYER_LANE, shaft_end2,
             (shaft_end2[0] - ARROW_HEAD_LEN, nb_y - ARROW_HEAD_W))

# ---------------------------------------------------------------------------
# 8. DIMENSIONS  (DIMENSIONS layer)
# ---------------------------------------------------------------------------
# Configure a custom dimstyle for mm labels at a readable size
# (duplicate the built-in "Standard" dimstyle and customise it)
doc.dimstyles.duplicate_entry("Standard", "ROAD_DIM")
ROAD_DIM = "ROAD_DIM"
road_ds = doc.dimstyles.get(ROAD_DIM)
road_ds.dxf.dimtxt   = 350     # text height (mm)
road_ds.dxf.dimasz   = 400     # arrow size  (mm)
road_ds.dxf.dimexo   = 200     # extension line offset
road_ds.dxf.dimexe   = 300     # extension line extension

DIM_GAP = 2_500   # gap below/left of geometry for dimension line

# 8a. Total road LENGTH  (horizontal, below the corridor)
dim_len = msp.add_linear_dim(
    base   = (X0, Y_BOTTOM_FOOTPATH - DIM_GAP),
    p1     = (X0,    Y_BOTTOM_FOOTPATH),
    p2     = (X_END, Y_BOTTOM_FOOTPATH),
    dimstyle = ROAD_DIM,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_len.set_text("200 000")          # explicit label in mm
dim_len.render()

# 8b. TOTAL CORRIDOR WIDTH  (vertical, right of corridor)
dim_w = msp.add_linear_dim(
    base   = (X_END + DIM_GAP, Y0),
    p1     = (X_END, Y_BOTTOM_FOOTPATH),
    p2     = (X_END, Y_TOP_FOOTPATH),
    angle  = 90,
    dimstyle = ROAD_DIM,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_w.set_text("11 000")
dim_w.render()

# 8c. CARRIAGEWAY WIDTH  (vertical, right of corridor, stacked)
dim_cw = msp.add_linear_dim(
    base   = (X_END + DIM_GAP * 2.8, Y0),
    p1     = (X_END, Y_LOWER_KERB),
    p2     = (X_END, Y_UPPER_KERB),
    angle  = 90,
    dimstyle = ROAD_DIM,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_cw.set_text("7 000 (Carriageway)")
dim_cw.render()

# 8d. FOOTPATH WIDTH – lower  (vertical)
dim_fp = msp.add_linear_dim(
    base   = (X_END + DIM_GAP * 5.0, Y0),
    p1     = (X_END, Y_BOTTOM_FOOTPATH),
    p2     = (X_END, Y_LOWER_KERB),
    angle  = 90,
    dimstyle = ROAD_DIM,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_fp.set_text("2 000 (Footpath)")
dim_fp.render()

# 8e. LANE WIDTH – south lane
dim_lane = msp.add_linear_dim(
    base   = (X0 - DIM_GAP * 2.5, Y0),
    p1     = (X0, Y_LOWER_KERB),
    p2     = (X0, Y_LANE_DIVIDER),
    angle  = 90,
    dimstyle = ROAD_DIM,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_lane.set_text("3 500 (Lane 1)")
dim_lane.render()

# 8f. LANE WIDTH – north lane
dim_lane2 = msp.add_linear_dim(
    base   = (X0 - DIM_GAP * 5.0, Y0),
    p1     = (X0, Y_LANE_DIVIDER),
    p2     = (X0, Y_UPPER_KERB),
    angle  = 90,
    dimstyle = ROAD_DIM,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_lane2.set_text("3 500 (Lane 2)")
dim_lane2.render()

# ---------------------------------------------------------------------------
# 9. ROAD LABELS  (TEXT layer)
# ---------------------------------------------------------------------------
TEXT_H_LARGE  = 500   # large heading (mm)
TEXT_H_NORMAL = 350   # normal annotation
TEXT_H_SMALL  = 280   # small notes
MID_X = (X0 + X_END) / 2   # horizontal centre of road

# Lane labels
add_text(LAYER_TEXT, "LANE 1  (Southbound  3.5 m)",
         (MID_X, Y_LOWER_KERB + LANE_W / 2),
         height=TEXT_H_NORMAL, halign="CENTER")

add_text(LAYER_TEXT, "LANE 2  (Northbound  3.5 m)",
         (MID_X, Y_LANE_DIVIDER + LANE_W / 2),
         height=TEXT_H_NORMAL, halign="CENTER")

# Footpath labels
add_text(LAYER_TEXT, "FOOTPATH  (2.0 m)",
         (MID_X, (Y_BOTTOM_FOOTPATH + Y_LOWER_KERB) / 2),
         height=TEXT_H_SMALL, halign="CENTER")

add_text(LAYER_TEXT, "FOOTPATH  (2.0 m)",
         (MID_X, (Y_UPPER_KERB + Y_TOP_FOOTPATH) / 2),
         height=TEXT_H_SMALL, halign="CENTER")

# Centreline label
add_text(LAYER_TEXT, "--- CENTRE LINE ---",
         (MID_X, Y_LANE_DIVIDER + 180),
         height=TEXT_H_SMALL, halign="CENTER")

# Road label (top)
add_text(LAYER_TEXT, "EXISTING TWO-WAY URBAN ROAD  (200 m Corridor)",
         (MID_X, Y_TOP_FOOTPATH + 1_200),
         height=TEXT_H_LARGE, halign="CENTER")

# ---------------------------------------------------------------------------
# 10. NORTH ARROW  (TEXT layer)
# ---------------------------------------------------------------------------
NA_X = X_END + 14_000
NA_Y = Y_TOP_FOOTPATH - 3_000
NA_SIZE = 2_000   # radius-like size

# Draw a simple north arrow: vertical shaft + arrowhead + "N" label
add_line(LAYER_TEXT, (NA_X, NA_Y - NA_SIZE), (NA_X, NA_Y + NA_SIZE))
# Arrowhead (pointing North = up)
add_line(LAYER_TEXT, (NA_X, NA_Y + NA_SIZE), (NA_X - 400, NA_Y + NA_SIZE - 800))
add_line(LAYER_TEXT, (NA_X, NA_Y + NA_SIZE), (NA_X + 400, NA_Y + NA_SIZE - 800))
# "N" label
add_text(LAYER_TEXT, "N", (NA_X - 200, NA_Y + NA_SIZE + 200), height=600)

# ---------------------------------------------------------------------------
# 11. SCALE NOTE  (TEXT layer)
# ---------------------------------------------------------------------------
add_text(LAYER_TEXT, "SCALE : 1:1000  (Plot on A1 / A0 sheet)",
         (X0, Y_BOTTOM_FOOTPATH - 5_000),
         height=TEXT_H_SMALL)

# ---------------------------------------------------------------------------
# 12. LEGEND  (TEXT layer)
# ---------------------------------------------------------------------------
LEG_X  = X0
LEG_Y  = Y_TOP_FOOTPATH + 3_500   # above road
LEG_SP = 1_200   # row spacing

add_text(LAYER_TEXT, "LEGEND", (LEG_X, LEG_Y), height=TEXT_H_NORMAL)

legend_items = [
    ("ROAD",          "Road & Carriageway Boundary  (Cyan, Continuous)"),
    ("LANE_MARKINGS", "Lane Centreline / Divider  (Yellow, Dashed)"),
    ("FOOTPATH",      "Footpath Area  (White, Hatched)"),
    ("DIMENSIONS",    "Dimension Lines  (Red, Continuous)"),
    ("TEXT",          "Annotation & Labels  (White, Continuous)"),
    ("TITLE_BLOCK",   "Title Block  (Blue, Continuous)"),
]
for i, (lname, ldesc) in enumerate(legend_items):
    row_y = LEG_Y - LEG_SP * (i + 1)
    # Colour swatch – short line
    add_line(LAYER_TEXT, (LEG_X, row_y + 150), (LEG_X + 1_200, row_y + 150))
    add_text(LAYER_TEXT, f"{lname} – {ldesc}",
             (LEG_X + 1_600, row_y), height=TEXT_H_SMALL)

# ---------------------------------------------------------------------------
# 13. TITLE BLOCK  (TITLE_BLOCK layer, in model space below the road)
# ---------------------------------------------------------------------------
TB_X  = X0
TB_Y  = Y_BOTTOM_FOOTPATH - 18_000   # below all dimension lines
TB_W  = ROAD_LENGTH                   # full width of road
TB_H  = 10_000                        # title block height

def tb_hline(y):
    hline(LAYER_TITLEBLOCK, TB_X, TB_X + TB_W, y)

def tb_vline(x):
    vline(LAYER_TITLEBLOCK, x, TB_Y, TB_Y + TB_H)

# Outer rectangle
msp.add_lwpolyline(
    [(TB_X, TB_Y), (TB_X + TB_W, TB_Y),
     (TB_X + TB_W, TB_Y + TB_H), (TB_X, TB_Y + TB_H), (TB_X, TB_Y)],
    close=True,
    dxfattribs={"layer": LAYER_TITLEBLOCK},
)

# Horizontal dividers at 2/5 and 4/5 of block height
tb_hline(TB_Y + TB_H * 0.4)
tb_hline(TB_Y + TB_H * 0.72)

# Vertical dividers splitting block into columns
COL1 = TB_X + TB_W * 0.35
COL2 = TB_X + TB_W * 0.65
tb_vline(COL1)
tb_vline(COL2)

# ---- Title block text ----
TB_TXT_H = 450

# Project title  (top row, full width, centred)
add_text(LAYER_TITLEBLOCK,
         "DESIGN OF AN INTEGRATED TRAFFIC CALMING SYSTEM",
         (TB_X + TB_W / 2, TB_Y + TB_H * 0.78 + 500),
         height=TB_TXT_H, halign="CENTER")
add_text(LAYER_TITLEBLOCK,
         "FOR ACCIDENT PREVENTION ON URBAN ROADS USING CAD",
         (TB_X + TB_W / 2, TB_Y + TB_H * 0.78),
         height=TB_TXT_H, halign="CENTER")

# Drawing title (second row)
add_text(LAYER_TITLEBLOCK,
         "Drawing: Existing Urban Road Corridor  (Plan View)",
         (TB_X + 500, TB_Y + TB_H * 0.44),
         height=400)

# Left column – project info
add_text(LAYER_TITLEBLOCK, "Project : BCV755A Road Safety Engineering",
         (TB_X + 300, TB_Y + TB_H * 0.44 - 1_000), height=320)
add_text(LAYER_TITLEBLOCK, "Module  : Final Year Project 2026",
         (TB_X + 300, TB_Y + TB_H * 0.44 - 1_600), height=320)

# Middle column – drawing info
add_text(LAYER_TITLEBLOCK, "Drawing No.  :  DWG-01",
         (COL1 + 300, TB_Y + TB_H * 0.44 - 500), height=320)
add_text(LAYER_TITLEBLOCK, "Scale        :  1:1000",
         (COL1 + 300, TB_Y + TB_H * 0.44 - 1_100), height=320)
add_text(LAYER_TITLEBLOCK, "Units        :  Millimetres",
         (COL1 + 300, TB_Y + TB_H * 0.44 - 1_700), height=320)
add_text(LAYER_TITLEBLOCK, "Sheet Size   :  A1 / A0",
         (COL1 + 300, TB_Y + TB_H * 0.44 - 2_300), height=320)

# Right column – revision / sign-off
add_text(LAYER_TITLEBLOCK, "Rev.  :  A  (Initial Issue)",
         (COL2 + 300, TB_Y + TB_H * 0.44 - 500), height=320)
add_text(LAYER_TITLEBLOCK, "Date  :  November 2026",
         (COL2 + 300, TB_Y + TB_H * 0.44 - 1_100), height=320)
add_text(LAYER_TITLEBLOCK, "Status : EXISTING CONDITIONS",
         (COL2 + 300, TB_Y + TB_H * 0.44 - 1_700), height=320)
add_text(LAYER_TITLEBLOCK, "Drawn :  _________________",
         (COL2 + 300, TB_Y + TB_H * 0.44 - 2_300), height=320)
add_text(LAYER_TITLEBLOCK, "Checked : ________________",
         (COL2 + 300, TB_Y + TB_H * 0.44 - 2_900), height=320)

# ---------------------------------------------------------------------------
# 14. Output path and save
# ---------------------------------------------------------------------------
# Navigate one level up from scripts/ to the project root, then into drawings/
SCRIPT_DIR   = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
OUTPUT_DIR   = os.path.join(PROJECT_ROOT, "drawings")
OUTPUT_FILE  = os.path.join(OUTPUT_DIR, "01_existing_urban_road.dxf")

os.makedirs(OUTPUT_DIR, exist_ok=True)

doc.saveas(OUTPUT_FILE)

# Verify the file was created
if os.path.isfile(OUTPUT_FILE):
    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"[OK] DXF saved successfully.")
    print(f"     Path : {OUTPUT_FILE}")
    print(f"     Size : {size_kb:.1f} KB")
else:
    print("[ERROR] File was NOT created.  Check write permissions.")
    sys.exit(1)
