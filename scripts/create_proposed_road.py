"""
=============================================================================
  create_proposed_road.py
  BCV755A Road Safety Engineering – Final Year Project
  Drawing : 02_proposed_traffic_calming_road.dxf
  Description : Proposed Urban Road with Integrated Traffic Calming Measures
  Units   : MILLIMETRES  (geometry at 1:1 scale)
  Plot scale  : 1:1000  (A3 landscape sheet, 420 mm × 297 mm)

  ANNOTATION SCALING RULE
  ───────────────────────
  Model-space text height = desired plotted height (mm) × SCALE (1000)

  Plotted targets
  ───────────────
   1.8 mm → 1800 mm   TH_TINY   – dense title-block fields
   2.0 mm → 2000 mm   TH_SMALL  – small notes, CL tag, signs
   2.5 mm → 2500 mm   TH_NORMAL – general annotation, dim text
   3.5 mm → 3500 mm   TH_SUB    – legend heading, lane labels, callouts
   4.0 mm → 4000 mm   TH_HEAD   – drawing heading, TB title lines
   5.0 mm → 5000 mm   TH_LARGE  – main road heading

  SHEET ZONES (all Y values listed bottom-to-top)
  ─────────────────────────────────────────────────
   10 000 – 75 000  : Title block   (65 mm plotted)
   75 000 – 80 000  : Gap
   80 000 –135 000  : Legend panel  (55 mm plotted)
  135 000 –160 000  : Gap + dim-line zone (road length dim at Y=160 000)
  160 000 –180 000  : External label zone below road
  180 000 –191 000  : ROAD CORRIDOR  (11 m = 11 mm plotted)
  191 000 –215 000  : Label & heading zone above road
  215 000 –250 000  : North-arrow zone
  250 000 –287 000  : Top margin (used for enlarged crossing detail)

  Horizontal zones (X, left → right)
  ────────────────────────────────────
   10 000 –  35 000  : Left dim Lane 2 stack (base X=35 000)
   35 000 –  55 000  : Left dim Lane 1 stack (base X=55 000)
   55 000 –  70 000  : Left annotation margin
   70 000 – 270 000  : ROAD CORRIDOR  (200 m)
  270 000 – 290 000  : Right annotation margin
  290 000 – 310 000  : Right dim Total-Width stack
  310 000 – 330 000  : Right dim Carriageway stack
  330 000 – 350 000  : Right dim Footpath stack
  350 000 – 390 000  : North-arrow zone
  390 000 – 410 000  : Right margin

  Install dependency (if missing):
      pip install ezdxf
=============================================================================
"""

# ---------------------------------------------------------------------------
# 0.  Imports and dependency check
# ---------------------------------------------------------------------------
import os
import sys
import math

try:
    import ezdxf
    from ezdxf import colors
    from ezdxf.enums import TextEntityAlignment
except ModuleNotFoundError:
    print("ezdxf is not installed.  Run:   pip install ezdxf")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 1.  Plot‑scale factor and text‑height constants
# ---------------------------------------------------------------------------
SCALE = 1000  # 1 : 1000

TH_TINY   = int(1.8 * SCALE)   # 1800 mm – dense TB fields
TH_SMALL  = int(2.0 * SCALE)   # 2000 mm – small notes, signs
TH_NORMAL = int(2.5 * SCALE)   # 2500 mm – general annotation / dim text
TH_SUB    = int(3.5 * SCALE)   # 3500 mm – sub‑headings, callouts
TH_HEAD   = int(4.0 * SCALE)   # 4000 mm – drawing heading, TB title rows
TH_LARGE  = int(5.0 * SCALE)   # 5000 mm – main road heading

# ---------------------------------------------------------------------------
# 2.  Road geometry constants (mm, 1:1 scale – same as previous drawings)
# ---------------------------------------------------------------------------
ROAD_LENGTH      = 200_000
CARRIAGEWAY_W    =   7_000   # 2 × 3 500
LANE_W           =   3_500
FOOTPATH_W       =   2_000
TOTAL_CORRIDOR_W =  11_000   # footpath + carriageway + footpath

# Anchor – bottom‑left of lower footpath
X0        = 70_000
Y_BOT_FP  = 180_000

# Derived Y‑coordinates
Y_LOW_KERB = Y_BOT_FP  + FOOTPATH_W        # 182 000
Y_LANE_DIV = Y_LOW_KERB + LANE_W           # 185 500 (centreline)
Y_UPP_KERB = Y_LOW_KERB + CARRIAGEWAY_W    # 189 000
Y_TOP_FP   = Y_BOT_FP  + TOTAL_CORRIDOR_W  # 191 000

X_END   = X0 + ROAD_LENGTH   # 270 000
MID_X   = (X0 + X_END) / 2   # 170 000

MID_Y_L1    = (Y_LOW_KERB + Y_LANE_DIV) / 2  # 183 750
MID_Y_L2    = (Y_LANE_DIV + Y_UPP_KERB) / 2  # 187 250

# ---------------------------------------------------------------------------
# 3.  DXF document
# ---------------------------------------------------------------------------

doc = ezdxf.new(dxfversion="R2010")
doc.header["$INSUNITS"] = 4   # mm

ezdxf.setup_linetypes(doc)

msp = doc.modelspace()

# ---------------------------------------------------------------------------
# 4.  Layers (including new traffic‑calming and sign layers)
# ---------------------------------------------------------------------------
LAYER_ROAD            = "ROAD"
LAYER_LANE            = "LANE_MARKINGS"
LAYER_FP              = "FOOTPATH"
LAYER_DIM             = "DIMENSIONS"
LAYER_TEXT            = "TEXT"
LAYER_TB              = "TITLE_BLOCK"
LAYER_LEG             = "LEGEND"
LAYER_TRAFFIC_CALMING = "TRAFFIC_CALMING"
LAYER_SIGNS           = "SIGNS"

LAYER_SPEC = [
    (LAYER_ROAD,            colors.CYAN,    "CONTINUOUS"),
    (LAYER_LANE,            colors.YELLOW,  "CENTER"),
    (LAYER_FP,              7,              "CONTINUOUS"),
    (LAYER_DIM,             colors.RED,     "CONTINUOUS"),
    (LAYER_TEXT,            colors.WHITE,   "CONTINUOUS"),
    (LAYER_TB,              colors.BLUE,    "CONTINUOUS"),
    (LAYER_LEG,             colors.MAGENTA, "CONTINUOUS"),
    (LAYER_TRAFFIC_CALMING, colors.GREEN,   "CONTINUOUS"),
    (LAYER_SIGNS,           colors.GREEN, "CONTINUOUS"),
]
for lname, lcol, llt in LAYER_SPEC:
    if doc.layers.has_entry(lname):
        lyr = doc.layers.get(lname)
        lyr.dxf.color    = lcol
        lyr.dxf.linetype = llt
    else:
        doc.layers.add(lname, dxfattribs={"color": lcol, "linetype": llt})

# ---------------------------------------------------------------------------
# 5.  Helper drawing functions
# ---------------------------------------------------------------------------

def hline(layer, x1, x2, y, ltype=None):
    attribs = {"layer": layer}
    if ltype:
        attribs["linetype"] = ltype
    msp.add_line((x1, y), (x2, y), dxfattribs=attribs)

def vline(layer, x, y1, y2, ltype=None):
    attribs = {"layer": layer}
    if ltype:
        attribs["linetype"] = ltype
    msp.add_line((x, y1), (x, y2), dxfattribs=attribs)

def add_text(layer, txt, insert, height=TH_NORMAL, rotation=0, halign="LEFT"):
    amap = {
        "LEFT":   TextEntityAlignment.LEFT,
        "CENTER": TextEntityAlignment.CENTER,
        "RIGHT":  TextEntityAlignment.RIGHT,
        "MIDDLE": TextEntityAlignment.MIDDLE_CENTER,
    }
    t = msp.add_text(txt, height=height, rotation=rotation,
                     dxfattribs={"layer": layer})
    t.set_placement(insert, align=amap.get(halign, TextEntityAlignment.LEFT))

def rect(layer, x, y, w, h):
    msp.add_lwpolyline(
        [(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
        close=True, dxfattribs={"layer": layer},
    )

# ---------------------------------------------------------------------------
# 6.  Sheet border (A3 landscape)
# ---------------------------------------------------------------------------
SHEET_W = 420_000
SHEET_H = 297_000
BORDER  = 10_000

rect("TITLE_BLOCK", 0, 0, SHEET_W, SHEET_H)               # outer trim (TB layer)
rect("TITLE_BLOCK", BORDER, BORDER,
     SHEET_W - 2 * BORDER, SHEET_H - 2 * BORDER)        # inner border

# ---------------------------------------------------------------------------
# 7.  ROAD geometry (Road layer)
# ---------------------------------------------------------------------------
hline(LAYER_ROAD, X0, X_END, Y_BOT_FP)   # bottom footpath edge
hline(LAYER_ROAD, X0, X_END, Y_TOP_FP)   # top footpath edge
vline(LAYER_ROAD, X0, Y_BOT_FP, Y_TOP_FP)   # left end cap
vline(LAYER_ROAD, X_END, Y_BOT_FP, Y_TOP_FP) # right end cap

# Kerb lines (footpath / carriageway boundary)
hline(LAYER_ROAD, X0, X_END, Y_LOW_KERB)   # lower kerb
hline(LAYER_ROAD, X0, X_END, Y_UPP_KERB)   # upper kerb

# ---------------------------------------------------------------------------
# 8.  FOOTPATH hatch (Footpath layer)
# ---------------------------------------------------------------------------
HATCH_SPACING = 5_000
for xi in range(X0, X_END, HATCH_SPACING):
    # lower footpath diagonal
    msp.add_line((xi, Y_BOT_FP), (xi + FOOTPATH_W, Y_LOW_KERB), dxfattribs={"layer": LAYER_FP})
    # upper footpath diagonal
    msp.add_line((xi, Y_UPP_KERB), (xi + FOOTPATH_W, Y_TOP_FP), dxfattribs={"layer": LAYER_FP})

hline(LAYER_FP, X0, X_END, Y_BOT_FP)
hline(LAYER_FP, X0, X_END, Y_TOP_FP)

# ---------------------------------------------------------------------------
# 9.  LANE MARKINGS (including direction arrows) – same as previous drawing
# ---------------------------------------------------------------------------
hline(LAYER_LANE, X0, X_END, Y_LANE_DIV, "DASHED")

ARROW_SPACING = 20_000
ARROW_LEN = 4_000
ARROW_HEAD_LEN = 1_500
ARROW_HEAD_W = 800

for xi in range(int(X0 + 35_000), int(X_END - 5_000), ARROW_SPACING):
    # Lane 1 – Southbound (←)
    sb_y = MID_Y_L1
    s_start = (xi + ARROW_LEN / 2, sb_y)
    s_end = (xi - ARROW_LEN / 2, sb_y)
    msp.add_line(s_start, s_end, dxfattribs={"layer": LAYER_LANE})
    msp.add_line(s_end, (s_end[0] + ARROW_HEAD_LEN, sb_y + ARROW_HEAD_W), dxfattribs={"layer": LAYER_LANE})
    msp.add_line(s_end, (s_end[0] + ARROW_HEAD_LEN, sb_y - ARROW_HEAD_W), dxfattribs={"layer": LAYER_LANE})

    # Lane 2 – Northbound (→)
    nb_y = MID_Y_L2
    n_start = (xi - ARROW_LEN / 2, nb_y)
    n_end = (xi + ARROW_LEN / 2, nb_y)
    msp.add_line(n_start, n_end, dxfattribs={"layer": LAYER_LANE})
    msp.add_line(n_end, (n_end[0] - ARROW_HEAD_LEN, nb_y + ARROW_HEAD_W), dxfattribs={"layer": LAYER_LANE})
    msp.add_line(n_end, (n_end[0] - ARROW_HEAD_LEN, nb_y - ARROW_HEAD_W), dxfattribs={"layer": LAYER_LANE})

# ---------------------------------------------------------------------------
# 10.  DIMENSIONS (Dimension style ROAD_DIM_V3 – same as previous)
# ---------------------------------------------------------------------------

doc.dimstyles.duplicate_entry("Standard", "ROAD_DIM_V3")
rd = doc.dimstyles.get("ROAD_DIM_V3")
rd.dxf.dimtxt = TH_NORMAL
rd.dxf.dimasz = 2_000
rd.dxf.dimexo = 1_500
rd.dxf.dimexe = 2_500
rd.dxf.dimgap = 1_000
DS = "ROAD_DIM_V3"

# Horizontal length dim (below road)

dim_len = msp.add_linear_dim(
    base=(MID_X, 160_000),
    p1=(X0, Y_BOT_FP),
    p2=(X_END, Y_BOT_FP),
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)

dim_len.set_text("200 000 mm  (200 m)")

dim_len.render()

# Vertical total width dim (right side)

dim_total = msp.add_linear_dim(
    base=(290_000, Y0 := 0),
    p1=(X_END, Y_BOT_FP),
    p2=(X_END, Y_TOP_FP),
    angle=90,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)

dim_total.set_text("11 000 mm  (Total Width)")

dim_total.render()

# Carriageway width dim

dim_cwy = msp.add_linear_dim(
    base=(310_000, 0),
    p1=(X_END, Y_LOW_KERB),
    p2=(X_END, Y_UPP_KERB),
    angle=90,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)

dim_cwy.set_text("7 000 mm  (Carriageway)")

dim_cwy.render()

# Footpath width dim

dim_fp = msp.add_linear_dim(
    base=(330_000, 0),
    p1=(X_END, Y_BOT_FP),
    p2=(X_END, Y_LOW_KERB),
    angle=90,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)

dim_fp.set_text("2 000 mm  (Footpath)")

dim_fp.render()

# Lane width dims (left side)

dim_l1 = msp.add_linear_dim(
    base=(55_000, 0),
    p1=(X0, Y_LOW_KERB),
    p2=(X0, Y_LANE_DIV),
    angle=90,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)

dim_l1.set_text("3 500 mm  (Lane 1)")

dim_l1.render()


dim_l2 = msp.add_linear_dim(
    base=(35_000, 0),
    p1=(X0, Y_LANE_DIV),
    p2=(X0, Y_UPP_KERB),
    angle=90,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)

dim_l2.set_text("3 500 mm  (Lane 2)")

dim_l2.render()

# ---------------------------------------------------------------------------
# 11.  ROAD ANNOTATIONS (Text layer)
# ---------------------------------------------------------------------------
# Title & scale note
add_text(LAYER_TEXT, "PROPOSED URBAN ROAD WITH INTEGRATED TRAFFIC CALMING MEASURES",
         (MID_X, 203_000), height=TH_LARGE, halign="CENTER")
add_text(LAYER_TEXT, "SCALE : 1:1000     UNITS : MILLIMETRES     SHEET : A3 LANDSCAPE",
         (MID_X, 198_000), height=TH_SMALL, halign="CENTER")

# Centreline tags
add_text(LAYER_TEXT, "C/L",
         (X0 - 1_500, Y_LANE_DIV + 400), height=TH_SMALL, halign="RIGHT")
add_text(LAYER_TEXT, "C/L",
         (X_END + 1_500, Y_LANE_DIV + 400), height=TH_SMALL, halign="LEFT")

# Footpath callouts (same as version 4)
FP_TOP_CALLOUT_X = MID_X
FP_TOP_LBL_Y = 193_500
msp.add_line((FP_TOP_CALLOUT_X, FP_TOP_LBL_Y - 400), (FP_TOP_CALLOUT_X, Y_TOP_FP), dxfattribs={"layer": LAYER_TEXT})
add_text(LAYER_TEXT, "FOOTPATH  (W = 2.0 m)", (FP_TOP_CALLOUT_X, FP_TOP_LBL_Y), height=TH_SMALL, halign="CENTER")

FP_BOT_CALLOUT_X = MID_X
FP_BOT_LBL_Y = 174_000
msp.add_line((FP_BOT_CALLOUT_X, FP_BOT_LBL_Y + TH_SMALL + 400), (FP_BOT_CALLOUT_X, Y_BOT_FP), dxfattribs={"layer": LAYER_TEXT})
add_text(LAYER_TEXT, "FOOTPATH  (W = 2.0 m)", (FP_BOT_CALLOUT_X, FP_BOT_LBL_Y), height=TH_SMALL, halign="CENTER")

# ---------------------------------------------------------------------------
# 12.  TRAFFIC CALMING FEATURES
# ---------------------------------------------------------------------------

def draw_crossing(chainage_mm, label_suffix):
    """Draw a raised pedestrian crossing (speed table) at given chainage.
    chainage_mm is distance from X0 (start of corridor)."""
    # X position of centre of crossing
    xc = X0 + chainage_mm
    # Width across carriageway (from lower kerb to upper kerb)
    table_width = CARRIAGEWAY_W
    # Length of crossing (along X) – choose 6 m (6 000 mm)
    table_len = 6_000
    # Define rectangle for raised table
    table_x0 = xc - table_len / 2
    table_y0 = Y_LOW_KERB
    rect(LAYER_TRAFFIC_CALMING, table_x0, table_y0, table_len, table_width)

    # Zebra crossing – series of short white lines across the table
    num_stripes = 7
    stripe_spacing = table_width / (num_stripes + 1)
    for i in range(1, num_stripes + 1):
        y_stripe = Y_LOW_KERB + i * stripe_spacing
        # draw a short line across the table width (full width)
        hline(LAYER_TRAFFIC_CALMING, table_x0, table_x0 + table_len, y_stripe, "DASHED")

    # Advance warning road markings (triangular pattern) 2 m upstream
    warn_x_start = xc - 2_000 - table_len / 2
    warn_x_end   = xc - 2_000
    hline(LAYER_TRAFFIC_CALMING, warn_x_start, warn_x_end, Y_LOW_KERB, "DASHED")
    hline(LAYER_TRAFFIC_CALMING, warn_x_start, warn_x_end, Y_UPP_KERB, "DASHED")

    # Warning signs – placed on footpaths outside road, 3 m left of road edge
    sign_offset = 3_000
    # Left side (southbound side footpath)
    left_sign_x = X0 - sign_offset
    left_sign_y = Y_LOW_KERB + table_width / 2
    rect(LAYER_SIGNS, left_sign_x - 1_500, left_sign_y - 1_500, 3_000, 3_000)
    add_text(LAYER_SIGNS, "WARN", (left_sign_x, left_sign_y), height=TH_SMALL, halign="CENTER")
    # Right side (northbound side footpath)
    right_sign_x = X0 - sign_offset
    right_sign_y = Y_UPP_KERB - table_width / 2
    rect(LAYER_SIGNS, right_sign_x - 1_500, right_sign_y - 1_500, 3_000, 3_000)
    add_text(LAYER_SIGNS, "WARN", (right_sign_x, right_sign_y), height=TH_SMALL, halign="CENTER")

    # Speed‑limit sign – placed further upstream (5 m before crossing) on left footpath
    speed_sign_x = xc - 5_000
    speed_sign_y = Y_LOW_KERB + table_width / 2
    rect(LAYER_SIGNS, speed_sign_x - 1_500, speed_sign_y - 1_500, 3_000, 3_000)
    add_text(LAYER_SIGNS, "SPEED 30", (speed_sign_x, speed_sign_y), height=TH_SMALL, halign="CENTER")

    # Reflective studs – placed along road edges every 20 m across the crossing length
    stud_spacing = 20_000
    num_studs = int(table_len // stud_spacing) + 1
    for i in range(num_studs):
        xs = table_x0 + i * stud_spacing
        # Left edge stud
        msp.add_circle((xs, Y_LOW_KERB), radius=200, dxfattribs={"layer": LAYER_TRAFFIC_CALMING})
        # Right edge stud
        msp.add_circle((xs, Y_UPP_KERB), radius=200, dxfattribs={"layer": LAYER_TRAFFIC_CALMING})

    # Callout for this crossing
    callout_x = xc + 20_000
    callout_y = Y_UPP_KERB + 10_000
    add_text(LAYER_TEXT, f"Crossing {label_suffix}", (callout_x, callout_y), height=TH_SUB, halign="LEFT")
    msp.add_line((callout_x, callout_y), (xc, Y_UPP_KERB), dxfattribs={"layer": LAYER_TEXT})

# Draw two crossings at the requested chainages
draw_crossing(60_000, "A")
draw_crossing(140_000, "B")

# ---------------------------------------------------------------------------
# 13.  NORTH ARROW (Text layer)
# ---------------------------------------------------------------------------
NA_X = 370_000
NA_Y = 228_000
NA_SIZE = 7_000
msp.add_line((NA_X, NA_Y - NA_SIZE), (NA_X, NA_Y + NA_SIZE), dxfattribs={"layer": LAYER_TEXT})
msp.add_line((NA_X, NA_Y + NA_SIZE), (NA_X - 1_500, NA_Y + NA_SIZE - 3_500), dxfattribs={"layer": LAYER_TEXT})
msp.add_line((NA_X, NA_Y + NA_SIZE), (NA_X + 1_500, NA_Y + NA_SIZE - 3_500), dxfattribs={"layer": LAYER_TEXT})
# Triangle base
msp.add_line((NA_X - 1_500, NA_Y + NA_SIZE - 3_500), (NA_X + 1_500, NA_Y + NA_SIZE - 3_500), dxfattribs={"layer": LAYER_TEXT})
# Circle base
msp.add_circle((NA_X, NA_Y - NA_SIZE), radius=1_200, dxfattribs={"layer": LAYER_TEXT})
add_text(LAYER_TEXT, "N", (NA_X, NA_Y + NA_SIZE + 1_500), height=TH_HEAD, halign="CENTER")
add_text(LAYER_TEXT, "NORTH", (NA_X, NA_Y - NA_SIZE - TH_SMALL - 1_000), height=TH_SMALL, halign="CENTER")

# ---------------------------------------------------------------------------
# 14.  LEGEND PANEL (same layout as version 4)
# ---------------------------------------------------------------------------
LEG_X = BORDER
LEG_Y = 80_000
LEG_W = SHEET_W - 2 * BORDER
LEG_H = 55_000
LEG_X_END = LEG_X + LEG_W
rect(LAYER_LEG, LEG_X, LEG_Y, LEG_W, LEG_H)
LEG_HEAD_Y = LEG_Y + LEG_H - 3_000
add_text(LAYER_LEG, "LEGEND", (LEG_X + 2_000, LEG_HEAD_Y), height=TH_HEAD)
hline(LAYER_LEG, LEG_X, LEG_X_END, LEG_HEAD_Y - 1_000)

LEG_ITEMS = [
    (LAYER_ROAD, "ROAD", "Road & carriageway boundaries (Cyan, Continuous)"),
    (LAYER_LANE, "LANE_MARKINGS", "Lane centreline / divider, direction arrows (Yellow, Dashed)"),
    (LAYER_FP, "FOOTPATH", "Footpath strips with diagonal hatch (White, Continuous)"),
    (LAYER_TRAFFIC_CALMING, "TRAFFIC_CALMING", "Raised pedestrian crossings, warning markings, studs"),
    (LAYER_SIGNS, "SIGNS", "Pedestrian warning & speed‑limit signs"),
    (LAYER_DIM, "DIMENSIONS", "Dimension lines and callout text (Red, Continuous)"),
    (LAYER_TEXT, "TEXT", "Annotation, labels, north arrow, callouts (White, Continuous)"),
    (LAYER_TB, "TITLE_BLOCK", "Title block border, sheet border (Blue, Continuous)"),
    (LAYER_LEG, "LEGEND", "Legend panel border and headings (Magenta, Continuous)"),
]
SWATCH_LEN = 8_000
LEG_ROW_H = int(TH_SMALL * 2.0)
LEG_ROW1_Y = LEG_HEAD_Y - 1_000 - 1_500
for i, (lyr, lyr_name, description) in enumerate(LEG_ITEMS):
    row_y = LEG_ROW1_Y - i * LEG_ROW_H
    msp.add_line((LEG_X + 2_000, row_y + TH_SMALL * 0.35),
                 (LEG_X + 2_000 + SWATCH_LEN, row_y + TH_SMALL * 0.35),
                 dxfattribs={"layer": lyr})
    add_text(LAYER_LEG, lyr_name, (LEG_X + 2_000 + SWATCH_LEN + 1_500, row_y), height=TH_SMALL)
    add_text(LAYER_LEG, description, (LEG_X + 2_000 + SWATCH_LEN + 55_000, row_y), height=TH_SMALL)

# ---------------------------------------------------------------------------
# 15.  TITLE BLOCK (same layout as version 4)
# ---------------------------------------------------------------------------
TB_X = BORDER
TB_Y = BORDER
TB_W = SHEET_W - 2 * BORDER
TB_H = 65_000
TB_END = TB_X + TB_W
TB_ROW_A_BOT = TB_Y
TB_ROW_A_TOP = TB_Y + int(TB_H * 0.60)
TB_ROW_B_BOT = TB_ROW_A_TOP
TB_ROW_B_TOP = TB_Y + int(TB_H * 0.75)
TB_ROW_C_BOT = TB_ROW_B_TOP
TB_ROW_C_TOP = TB_Y + TB_H
TB_COL1_X = TB_X
TB_COL2_X = TB_X + TB_W // 3
TB_COL3_X = TB_X + 2 * (TB_W // 3)

rect(LAYER_TB, TB_X, TB_Y, TB_W, TB_H)
hline(LAYER_TB, TB_X, TB_END, TB_ROW_A_TOP)
hline(LAYER_TB, TB_X, TB_END, TB_ROW_B_TOP)
vline(LAYER_TB, TB_COL2_X, TB_ROW_A_BOT, TB_ROW_A_TOP)
vline(LAYER_TB, TB_COL3_X, TB_ROW_A_BOT, TB_ROW_A_TOP)

# Row C – Project title
ROW_C_MID = (TB_ROW_C_BOT + TB_ROW_C_TOP) / 2
ROW_C_LINE_H = TH_HEAD * 1.4
add_text(LAYER_TB, "DESIGN OF AN INTEGRATED TRAFFIC CALMING SYSTEM",
         (TB_X + TB_W / 2, ROW_C_MID + ROW_C_LINE_H / 2 - TH_HEAD * 0.4),
         height=TH_HEAD, halign="CENTER")
add_text(LAYER_TB, "FOR ACCIDENT PREVENTION ON URBAN ROADS USING CAD",
         (TB_X + TB_W / 2, ROW_C_MID - ROW_C_LINE_H / 2 - TH_HEAD * 0.4),
         height=TH_HEAD, halign="CENTER")

# Row B – Drawing title
ROW_B_MID = (TB_ROW_B_BOT + TB_ROW_B_TOP) / 2
add_text(LAYER_TB,
         "DRAWING NO. DWG-02   |   Proposed Urban Road with Traffic Calming  –  Plan View   |   Sheet 1 of 1",
         (TB_X + TB_W / 2, int(ROW_B_MID - TH_NORMAL * 0.5)),
         height=TH_NORMAL, halign="CENTER")

# Row A – Fields (project info, drawing details, revision)
FIELD_H = TH_TINY
FIELD_LINE = int(FIELD_H * 2.1)
FIELD_TOP = TB_ROW_A_TOP - 2_000
MARGIN_L = 1_500

def tb_field(col_x, idx, label, value):
    y = FIELD_TOP - idx * FIELD_LINE
    add_text(LAYER_TB, label, (col_x + MARGIN_L, y), height=FIELD_H)
    add_text(LAYER_TB, value, (col_x + MARGIN_L + 35_000, y), height=FIELD_H)

# Column 1 – Project information
col1_data = [
    ("Project  :", "BCV755A Road Safety Engineering"),
    ("Title    :", "Traffic Calming System Design"),
    ("Module   :", "Road Safety Engineering"),
    ("Institution:", "_______________________"),
    ("Student  :", "_______________________"),
    ("Reg. No. :", "_______________________"),
    ("Supervisor:", "_______________________"),
]
for i, (l, v) in enumerate(col1_data):
    tb_field(TB_COL1_X, i, l, v)

# Column 2 – Drawing details
col2_data = [
    ("Drawing No. :", "DWG-02"),
    ("Title       :", "Proposed Road with Traffic Calming"),
    ("Scale       :", "1 : 1000"),
    ("Units       :", "Millimetres  (mm)"),
    ("Sheet Size  :", "A3 Landscape"),
    ("Drawn by    :", "_______________"),
    ("Date Drawn  :", "_______________"),
]
for i, (l, v) in enumerate(col2_data):
    tb_field(TB_COL2_X, i, l, v)

# Column 3 – Revision and approval
col3_data = [
    ("Revision  :", "A  –  Initial Issue"),
    ("Status    :", "PROPOSED DESIGN"),
    ("Date      :", "November  2026"),
    ("Checked by:", "_______________"),
    ("Approved  :", "_______________"),
    ("File Ref. :", "DWG-02-PROPOSED-ROAD"),
    ("CAD Ref.  :", "BCV755A-DWG-02"),
]
for i, (l, v) in enumerate(col3_data):
    tb_field(TB_COL3_X, i, l, v)

# ---------------------------------------------------------------------------
# 16.  ENLARGED DETAIL – typical crossing (placed in top‑margin area)
# ---------------------------------------------------------------------------
DETAIL_X0 = X0 + 30_000   # somewhat left of centre
DETAIL_Y0 = 260_000       # within top margin (250k‑287k)
DETAIL_W  = 30_000
DETAIL_H  = 40_000
# Outline box for the detail
rect(LAYER_TEXT, DETAIL_X0, DETAIL_Y0, DETAIL_W, DETAIL_H)
# Inside the box, draw a simplified crossing (same geometry as draw_crossing)
# Use a smaller scale: table length 3 m, width full carriageway
c_x = DETAIL_X0 + DETAIL_W / 2
c_y = DETAIL_Y0 + DETAIL_H / 2
tbl_len = 3_000
rect(LAYER_TRAFFIC_CALMING, c_x - tbl_len/2, Y_LOW_KERB, tbl_len, CARRIAGEWAY_W)
# Zebra stripes (3 stripes)
for i in range(1, 4):
    y_str = Y_LOW_KERB + i * CARRIAGEWAY_W / 4
    hline(LAYER_TRAFFIC_CALMING, c_x - tbl_len/2, c_x + tbl_len/2, y_str, "DASHED")
# Annotation
add_text(LAYER_TEXT, "TYPICAL CROSSING DETAIL - CONCEPTUAL",
         (c_x, DETAIL_Y0 + DETAIL_H - 1_500), height=TH_SUB, halign="CENTER")

# ---------------------------------------------------------------------------
# 17.  Simple collision detection for TEXT entities (reuse from version 4)
# ---------------------------------------------------------------------------
def check_collisions():
    texts = list(msp.query('TEXT'))
    max_iter = 10
    for _ in range(max_iter):
        moved = False
        for i in range(len(texts)):
            ti = texts[i]
            xi, yi = ti.dxf.insert.x, ti.dxf.insert.y
            hi = ti.dxf.height
            bb_i = (xi - hi/2, xi + hi/2, yi - hi/2, yi + hi/2)
            for j in range(i+1, len(texts)):
                tj = texts[j]
                xj, yj = tj.dxf.insert.x, tj.dxf.insert.y
                hj = tj.dxf.height
                bb_j = (xj - hj/2, xj + hj/2, yj - hj/2, yj + hj/2)
                if not (bb_i[1] < bb_j[0] or bb_i[0] > bb_j[1] or bb_i[3] < bb_j[2] or bb_i[2] > bb_j[3]):
                    # shift later text leftwards
                    new_xj = xj - 5_000
                    tj.set_placement((new_xj, yj), align=TextEntityAlignment.LEFT)
                    moved = True
        if not moved:
            break
    else:
        print("[WARNING] Collision detection reached max iterations; some overlaps may remain.")

check_collisions()

# ---------------------------------------------------------------------------
# 18.  Save DXF (do not touch previous drawings)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "drawings")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "02_proposed_traffic_calming_road.dxf")

os.makedirs(OUTPUT_DIR, exist_ok=True)

doc.saveas(OUTPUT_FILE)

if os.path.isfile(OUTPUT_FILE):
    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"[OK]  DXF saved successfully.")
    print(f"      Path : {OUTPUT_FILE}")
    print(f"      Size : {size_kb:.1f} KB")
else:
    print("[ERROR] File was NOT created.")
    sys.exit(1)
