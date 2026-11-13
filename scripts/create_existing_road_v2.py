"""
=============================================================================
  create_existing_road_v2.py
  BCV755A Road Safety Engineering – Final Year Project
  Title : Design of an Integrated Traffic Calming System for Accident
          Prevention on Urban Roads Using CAD
  Drawing : 01_existing_urban_road_v2.dxf  –  Existing Urban Road Corridor
  Author  : Final Year Engineering Student
  Units   : MILLIMETRES  (all geometry at 1:1 scale)
  Plot scale intended: 1:1000  (on A1 / A0 sheet)
  Layers  : ROAD | LANE_MARKINGS | FOOTPATH | DIMENSIONS | TEXT | TITLE_BLOCK

  ANNOTATION SCALING RULE
  -----------------------
  At a plot scale of 1:1000 every model-space length appears 1000× smaller
  on paper.  To achieve a desired plotted text height T (mm), the model-space
  height must be:
       model_height = T  ×  SCALE   (where SCALE = 1000)

  Plotted targets used in this drawing
  ─────────────────────────────────────
   2.0 mm → 2000 mm model  (small notes, title-block fields)
   2.5 mm → 2500 mm model  (normal annotation)
   3.5 mm → 3500 mm model  (sub-headings, lane labels)
   5.0 mm → 5000 mm model  (road heading above corridor)
   7.0 mm → 7000 mm model  (project title in title block)

  Dimension text: 2.5 mm plotted → 2500 mm model
  Arrows        : 2.0 mm plotted → 2000 mm model

  Install dependency (if missing):
      pip install ezdxf
=============================================================================
"""

# ---------------------------------------------------------------------------
# 0.  Imports and dependency check
# ---------------------------------------------------------------------------
import os
import sys

try:
    import ezdxf
    from ezdxf import colors
    from ezdxf.enums import TextEntityAlignment
except ModuleNotFoundError:
    print("ezdxf is not installed.  Run:   pip install ezdxf")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 1.  Plot-scale factor
#     All annotation sizes are expressed in plotted mm then multiplied by S.
#     Road geometry is NOT multiplied – it stays in real-world mm.
# ---------------------------------------------------------------------------
S = 1000   # 1:1000 plot scale

# Plotted text heights  →  model-space heights
TH_SMALL   = int(2.0 * S)   # 2000 mm  – small notes / title-block fields
TH_NORMAL  = int(2.5 * S)   # 2500 mm  – normal annotation
TH_SUBHEAD = int(3.5 * S)   # 3500 mm  – sub-headings, lane labels
TH_HEAD    = int(5.0 * S)   # 5000 mm  – road heading
TH_TITLE   = int(7.0 * S)   # 7000 mm  – project title in title block

# ---------------------------------------------------------------------------
# 2.  Road geometry constants  (millimetres, 1:1 — UNCHANGED from v1)
# ---------------------------------------------------------------------------
ROAD_LENGTH      = 200_000   # 200 m  corridor length  (X-axis)
CARRIAGEWAY_W    =   7_000   # 7 m   two-way carriageway
LANE_W           =   3_500   # 3.5 m single-lane width
FOOTPATH_W       =   2_000   # 2 m   footpath each side
TOTAL_CORRIDOR_W =  11_000   # 11 m  total corridor width

# Origin – lower-left corner of the lower footpath
X0, Y0 = 20_000, 50_000     # generous margin so dimensions don't clip origin

# Key Y-coordinates
Y_BOT_FP    = Y0                              # bottom of lower footpath
Y_LOW_KERB  = Y0 + FOOTPATH_W               # bottom kerb line   (Y0+2000)
Y_LANE_DIV  = Y_LOW_KERB + LANE_W           # lane centreline    (Y0+5500)
Y_UPP_KERB  = Y_LOW_KERB + CARRIAGEWAY_W   # top kerb line      (Y0+9000)
Y_TOP_FP    = Y0 + TOTAL_CORRIDOR_W         # top of upper footpath (Y0+11000)

X_END = X0 + ROAD_LENGTH                    # right end of corridor

# Corridor mid-points
MID_X = (X0 + X_END) / 2
MID_Y_LANE1 = Y_LOW_KERB  + LANE_W / 2     # centre of south lane
MID_Y_LANE2 = Y_LANE_DIV  + LANE_W / 2     # centre of north lane
MID_Y_FP_BOT = (Y_BOT_FP  + Y_LOW_KERB) / 2
MID_Y_FP_TOP = (Y_UPP_KERB + Y_TOP_FP) / 2

# ---------------------------------------------------------------------------
# 3.  DXF document
# ---------------------------------------------------------------------------
doc = ezdxf.new(dxfversion="R2010")
doc.header["$INSUNITS"] = 4   # millimetres
doc.header["$LUNITS"]   = 2   # decimal
doc.header["$LUPREC"]   = 0   # 0 decimal places

ezdxf.setup_linetypes(doc)    # load DASHED, CENTER, etc.

msp = doc.modelspace()

# ---------------------------------------------------------------------------
# 4.  Layer definitions
# ---------------------------------------------------------------------------
LAYER_ROAD   = "ROAD"
LAYER_LANE   = "LANE_MARKINGS"
LAYER_FP     = "FOOTPATH"
LAYER_DIM    = "DIMENSIONS"
LAYER_TEXT   = "TEXT"
LAYER_TB     = "TITLE_BLOCK"

LAYER_SPEC = [
    # (name,        ACI colour,     linetype)
    (LAYER_ROAD,  colors.CYAN,    "CONTINUOUS"),
    (LAYER_LANE,  colors.YELLOW,  "CENTER"),
    (LAYER_FP,    7,              "CONTINUOUS"),   # 7 = white / black
    (LAYER_DIM,   colors.RED,     "CONTINUOUS"),
    (LAYER_TEXT,  colors.WHITE,   "CONTINUOUS"),
    (LAYER_TB,    colors.BLUE,    "CONTINUOUS"),
]

for lname, lcol, llt in LAYER_SPEC:
    if doc.layers.has_entry(lname):
        lyr = doc.layers.get(lname)
        lyr.dxf.color   = lcol
        lyr.dxf.linetype = llt
    else:
        doc.layers.add(lname, dxfattribs={"color": lcol, "linetype": llt})

# ---------------------------------------------------------------------------
# 5.  Helper drawing functions
# ---------------------------------------------------------------------------

def hline(layer, x1, x2, y, ltype=None):
    """Draw a horizontal line."""
    attribs = {"layer": layer}
    if ltype:
        attribs["linetype"] = ltype
    msp.add_line((x1, y), (x2, y), dxfattribs=attribs)


def vline(layer, x, y1, y2, ltype=None):
    """Draw a vertical line."""
    attribs = {"layer": layer}
    if ltype:
        attribs["linetype"] = ltype
    msp.add_line((x, y1), (x, y2), dxfattribs=attribs)


def add_text(layer, text, insert, height=TH_NORMAL, rotation=0, halign="LEFT"):
    """Add a TEXT entity with alignment."""
    amap = {
        "LEFT":   TextEntityAlignment.LEFT,
        "CENTER": TextEntityAlignment.CENTER,
        "RIGHT":  TextEntityAlignment.RIGHT,
        "MIDDLE": TextEntityAlignment.MIDDLE_CENTER,
    }
    t = msp.add_text(text, height=height, rotation=rotation,
                     dxfattribs={"layer": layer})
    t.set_placement(insert, align=amap.get(halign, TextEntityAlignment.LEFT))


def add_mtext(layer, text, insert, char_height=TH_NORMAL, width=0):
    """Add an MTEXT entity (multi-line capable with \\P)."""
    msp.add_mtext(text, dxfattribs={
        "layer": layer, "insert": insert,
        "char_height": char_height, "width": width,
    })


# ---------------------------------------------------------------------------
# 6.  Road corridor geometry  (ROAD layer)
# ---------------------------------------------------------------------------
# Outer boundary lines
hline(LAYER_ROAD, X0, X_END, Y_BOT_FP)    # bottom outer edge
hline(LAYER_ROAD, X0, X_END, Y_TOP_FP)    # top outer edge
vline(LAYER_ROAD, X0,    Y_BOT_FP, Y_TOP_FP)   # left end
vline(LAYER_ROAD, X_END, Y_BOT_FP, Y_TOP_FP)   # right end

# Kerb lines (carriageway / footpath boundaries)
hline(LAYER_ROAD, X0, X_END, Y_LOW_KERB)   # lower kerb
hline(LAYER_ROAD, X0, X_END, Y_UPP_KERB)   # upper kerb

# ---------------------------------------------------------------------------
# 7.  Footpath hatch lines  (FOOTPATH layer)
# ---------------------------------------------------------------------------
# Diagonal hatch every 5 m to indicate paved footpath
HATCH_SPACING = 5_000   # mm between hatch lines
for xi in range(X0, X_END, HATCH_SPACING):
    # Lower footpath strip  (diagonal bottom-left → top-right)
    msp.add_line((xi, Y_BOT_FP),  (xi + FOOTPATH_W, Y_LOW_KERB),
                 dxfattribs={"layer": LAYER_FP})
    # Upper footpath strip
    msp.add_line((xi, Y_UPP_KERB), (xi + FOOTPATH_W, Y_TOP_FP),
                 dxfattribs={"layer": LAYER_FP})

# Reinforce footpath outer edges
hline(LAYER_FP, X0, X_END, Y_BOT_FP)
hline(LAYER_FP, X0, X_END, Y_TOP_FP)

# ---------------------------------------------------------------------------
# 8.  Lane markings  (LANE_MARKINGS layer)
# ---------------------------------------------------------------------------
# Centre / lane-divider line  (DASHED linetype for lane marking)
hline(LAYER_LANE, X0, X_END, Y_LANE_DIV, "DASHED")

# Direction arrows – scaled so they are visible at 1:1000
# At 1:1000: 1500 mm model = 1.5 mm plotted shaft, visible and not crowded.
ARROW_SPACING  = 20_000   # every 20 m
ARROW_LEN      =  4_000   # shaft length in model mm
ARROW_HEAD_LEN =  1_500   # arrowhead leg length
ARROW_HEAD_W   =    800   # arrowhead half-width

for xi in range(int(X0 + 15_000), int(X_END - 5_000), ARROW_SPACING):
    # Lane 1  –  Southbound (bottom lane, arrow points ←)
    sb_y = MID_Y_LANE1
    s_start = (xi + ARROW_LEN / 2, sb_y)
    s_end   = (xi - ARROW_LEN / 2, sb_y)
    msp.add_line(s_start, s_end, dxfattribs={"layer": LAYER_LANE})
    msp.add_line(s_end, (s_end[0] + ARROW_HEAD_LEN, sb_y + ARROW_HEAD_W),
                 dxfattribs={"layer": LAYER_LANE})
    msp.add_line(s_end, (s_end[0] + ARROW_HEAD_LEN, sb_y - ARROW_HEAD_W),
                 dxfattribs={"layer": LAYER_LANE})

    # Lane 2  –  Northbound (top lane, arrow points →)
    nb_y = MID_Y_LANE2
    n_start = (xi - ARROW_LEN / 2, nb_y)
    n_end   = (xi + ARROW_LEN / 2, nb_y)
    msp.add_line(n_start, n_end, dxfattribs={"layer": LAYER_LANE})
    msp.add_line(n_end, (n_end[0] - ARROW_HEAD_LEN, nb_y + ARROW_HEAD_W),
                 dxfattribs={"layer": LAYER_LANE})
    msp.add_line(n_end, (n_end[0] - ARROW_HEAD_LEN, nb_y - ARROW_HEAD_W),
                 dxfattribs={"layer": LAYER_LANE})

# ---------------------------------------------------------------------------
# 9.  Dimension style  (DIMENSIONS layer)
#     dimtxt = 2500 mm model  →  2.5 mm plotted at 1:1000
# ---------------------------------------------------------------------------
doc.dimstyles.duplicate_entry("Standard", "ROAD_DIM")
rd = doc.dimstyles.get("ROAD_DIM")
rd.dxf.dimtxt   = TH_NORMAL   # 2500 mm – dimension number height
rd.dxf.dimasz   = 2_000       # 2.0 mm plotted arrow size
rd.dxf.dimexo   = 1_500       # extension line offset from point
rd.dxf.dimexe   = 2_500       # extension line overshoot past dim line
rd.dxf.dimgap   = 1_000       # gap between dim line and text

DSTYLE = "ROAD_DIM"

# Clearances for dimension placement (in model mm = plotted mm × 1000)
# 10 mm plotted gap → 10 000 mm model
DIM_GAP   = 12_000    # first dim line offset from road edge
DIM_STACK = 14_000    # spacing between stacked dim lines

# ---- 9a. Road LENGTH  (horizontal, below the corridor) ----
dim_len = msp.add_linear_dim(
    base = (X0, Y_BOT_FP - DIM_GAP),
    p1   = (X0,    Y_BOT_FP),
    p2   = (X_END, Y_BOT_FP),
    dimstyle   = DSTYLE,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_len.set_text("200 000 mm  (200 m)")
dim_len.render()

# ---- 9b. Total CORRIDOR WIDTH (vertical, right of corridor) ----
dim_cw = msp.add_linear_dim(
    base = (X_END + DIM_GAP, Y0),
    p1   = (X_END, Y_BOT_FP),
    p2   = (X_END, Y_TOP_FP),
    angle      = 90,
    dimstyle   = DSTYLE,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_cw.set_text("11 000 mm  (Total Width)")
dim_cw.render()

# ---- 9c. CARRIAGEWAY width (vertical, further right) ----
dim_cr = msp.add_linear_dim(
    base = (X_END + DIM_GAP + DIM_STACK * 1.6, Y0),
    p1   = (X_END, Y_LOW_KERB),
    p2   = (X_END, Y_UPP_KERB),
    angle      = 90,
    dimstyle   = DSTYLE,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_cr.set_text("7 000 mm  (Carriageway)")
dim_cr.render()

# ---- 9d. Lower FOOTPATH width (vertical, further right) ----
dim_fp_lo = msp.add_linear_dim(
    base = (X_END + DIM_GAP + DIM_STACK * 3.4, Y0),
    p1   = (X_END, Y_BOT_FP),
    p2   = (X_END, Y_LOW_KERB),
    angle      = 90,
    dimstyle   = DSTYLE,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_fp_lo.set_text("2 000 mm  (Footpath)")
dim_fp_lo.render()

# ---- 9e. LANE 1 width (vertical, left of corridor) ----
dim_l1 = msp.add_linear_dim(
    base = (X0 - DIM_GAP, Y0),
    p1   = (X0, Y_LOW_KERB),
    p2   = (X0, Y_LANE_DIV),
    angle      = 90,
    dimstyle   = DSTYLE,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_l1.set_text("3 500 mm  (Lane 1)")
dim_l1.render()

# ---- 9f. LANE 2 width (vertical, further left) ----
dim_l2 = msp.add_linear_dim(
    base = (X0 - DIM_GAP - DIM_STACK * 1.8, Y0),
    p1   = (X0, Y_LANE_DIV),
    p2   = (X0, Y_UPP_KERB),
    angle      = 90,
    dimstyle   = DSTYLE,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_l2.set_text("3 500 mm  (Lane 2)")
dim_l2.render()

# ---------------------------------------------------------------------------
# 10.  Road annotations  (TEXT layer)
#      All heights are in model-mm; see TH_* constants defined at top.
# ---------------------------------------------------------------------------

# ── Road heading (above corridor) ──────────────────────────────────────────
HEAD_Y = Y_TOP_FP + 6_000   # 6 mm plotted gap above footpath top
add_text(LAYER_TEXT,
         "EXISTING TWO-WAY URBAN ROAD  –  200 m CORRIDOR  (PLAN VIEW)",
         (MID_X, HEAD_Y),
         height=TH_HEAD, halign="CENTER")

# ── Lane labels ─────────────────────────────────────────────────────────────
# Placed at lane mid-height; lane is 3500 mm wide  →  2.5 mm plotted text fits
add_text(LAYER_TEXT, "LANE 1  –  SOUTHBOUND  (3.5 m)",
         (MID_X, MID_Y_LANE1 - TH_SUBHEAD / 2),
         height=TH_SUBHEAD, halign="CENTER")

add_text(LAYER_TEXT, "LANE 2  –  NORTHBOUND  (3.5 m)",
         (MID_X, MID_Y_LANE2 - TH_SUBHEAD / 2),
         height=TH_SUBHEAD, halign="CENTER")

# ── Footpath labels  (rotated 0°; centred along road, in footpath strip) ──
# 2000 mm strip = 2 mm plotted.  Use TH_NORMAL (2500 mm) text,
# placed at centre of strip; slight overflow is acceptable in CAD convention.
add_text(LAYER_TEXT, "FOOTPATH  (W = 2.0 m)",
         (MID_X, MID_Y_FP_BOT - TH_NORMAL / 2),
         height=TH_NORMAL, halign="CENTER")

add_text(LAYER_TEXT, "FOOTPATH  (W = 2.0 m)",
         (MID_X, MID_Y_FP_TOP - TH_NORMAL / 2),
         height=TH_NORMAL, halign="CENTER")

# ── Centreline label ────────────────────────────────────────────────────────
# Place just below the lane-divider line to avoid overlap with arrows
CL_LABEL_X = X0 + 8_000    # near left end, clear of arrows
add_text(LAYER_TEXT, "C/L",
         (CL_LABEL_X, Y_LANE_DIV + 400),
         height=TH_SMALL)

# ── Scale note ──────────────────────────────────────────────────────────────
SCALE_Y = Y_BOT_FP - DIM_GAP - DIM_STACK * 0.9   # below length dimension
add_text(LAYER_TEXT,
         "DRAWING SCALE :  1:1000     UNITS :  MILLIMETRES     SHEET :  A1 / A0",
         (MID_X, SCALE_Y),
         height=TH_NORMAL, halign="CENTER")

# ---------------------------------------------------------------------------
# 11.  North Arrow  (TEXT layer)
#      At 1:1000 the arrow must be ~8–10 mm plotted → 8000–10000 mm model
# ---------------------------------------------------------------------------
NA_X    = X_END + 55_000    # well clear of rightmost dimension stack
NA_Y    = Y_LOW_KERB + CARRIAGEWAY_W / 2   # vertically centred on road
NA_SIZE = 8_000              # 8 mm plotted half-length

# Shaft
msp.add_line((NA_X, NA_Y - NA_SIZE), (NA_X, NA_Y + NA_SIZE),
             dxfattribs={"layer": LAYER_TEXT})
# Arrowhead  (filled look with two lines)
msp.add_line((NA_X, NA_Y + NA_SIZE),
             (NA_X - 1_500, NA_Y + NA_SIZE - 3_000),
             dxfattribs={"layer": LAYER_TEXT})
msp.add_line((NA_X, NA_Y + NA_SIZE),
             (NA_X + 1_500, NA_Y + NA_SIZE - 3_000),
             dxfattribs={"layer": LAYER_TEXT})
# Circle base
msp.add_circle((NA_X, NA_Y), radius=1_200,
               dxfattribs={"layer": LAYER_TEXT})
# "N" label
add_text(LAYER_TEXT, "N",
         (NA_X - TH_SUBHEAD * 0.3, NA_Y + NA_SIZE + 1_500),
         height=TH_SUBHEAD, halign="CENTER")
# Box label below
add_text(LAYER_TEXT, "NORTH",
         (NA_X, NA_Y - NA_SIZE - 2_500),
         height=TH_SMALL, halign="CENTER")

# ---------------------------------------------------------------------------
# 12.  Legend  (TEXT layer)
#      Placed above the road heading, left-aligned
# ---------------------------------------------------------------------------
LEG_X  = X0
LEG_Y  = HEAD_Y + TH_HEAD + 8_000   # above road heading with gap
LEG_ROW = TH_NORMAL * 1.6            # row spacing  (~1.6× text height)

legend_items = [
    (LAYER_ROAD,  colors.CYAN,   "Road & Carriageway Boundary  (Cyan, Continuous)"),
    (LAYER_LANE,  colors.YELLOW, "Lane Centreline / Divider  (Yellow, DASHED CENTER)"),
    (LAYER_FP,    7,             "Footpath Area  (White, Diagonal Hatch)"),
    (LAYER_DIM,   colors.RED,    "Dimension Lines & Text  (Red, Continuous)"),
    (LAYER_TEXT,  colors.WHITE,  "Annotation, Labels & North Arrow  (White)"),
    (LAYER_TB,    colors.BLUE,   "Title Block  (Blue, Continuous)"),
]

# Legend heading
add_text(LAYER_TEXT, "LEGEND", (LEG_X, LEG_Y), height=TH_SUBHEAD)

SWATCH_LEN = 6_000   # length of colour-swatch line = 6 mm plotted

for i, (_, _, desc) in enumerate(legend_items):
    row_y = LEG_Y - LEG_ROW * (i + 1)
    # Swatch line (use TEXT layer – colour is per-layer in CAD)
    msp.add_line((LEG_X, row_y + TH_NORMAL * 0.3),
                 (LEG_X + SWATCH_LEN, row_y + TH_NORMAL * 0.3),
                 dxfattribs={"layer": LAYER_TEXT})
    # Description
    add_text(LAYER_TEXT, desc,
             (LEG_X + SWATCH_LEN + 1_500, row_y),
             height=TH_NORMAL)

# ---------------------------------------------------------------------------
# 13.  Title Block  (TITLE_BLOCK layer)
#      Placed below all dimension lines, full corridor width.
#      At 1:1000:  TB_H=70000mm → 70mm plotted  –  clearly readable.
# ---------------------------------------------------------------------------
TB_X = X0
TB_Y = Y_BOT_FP - 85_000    # ~85 mm plotted below footpath bottom
TB_W = ROAD_LENGTH           # 200 mm plotted  (matches road length)
TB_H = 70_000                # 70 mm plotted height

def tbl_h(y):
    """Draw a full-width horizontal rule inside the title block."""
    hline(LAYER_TB, TB_X, TB_X + TB_W, y)

def tbl_v(x):
    """Draw a full-height vertical rule inside the title block."""
    vline(LAYER_TB, x, TB_Y, TB_Y + TB_H)

# Outer border
msp.add_lwpolyline(
    [(TB_X, TB_Y), (TB_X + TB_W, TB_Y),
     (TB_X + TB_W, TB_Y + TB_H), (TB_X, TB_Y + TB_H)],
    close=True, dxfattribs={"layer": LAYER_TB},
)

# ── Row divisions (3 rows) ──────────────────────────────────────────────────
# Row 3 (top)   : Project title band  –  top 25% of block
# Row 2 (mid)   : Drawing title band  –  next 20%
# Row 1 (bot)   : Field data          –  bottom 55%
R3_Y = TB_Y + TB_H * 0.75   # top band bottom edge
R2_Y = TB_Y + TB_H * 0.55   # mid band bottom edge
tbl_h(R3_Y)
tbl_h(R2_Y)

# ── Column divisions (bottom row only: 3 equal columns) ────────────────────
C1_X = TB_X + TB_W * 0.33
C2_X = TB_X + TB_W * 0.66
vline(LAYER_TB, C1_X, TB_Y, R2_Y)
vline(LAYER_TB, C2_X, TB_Y, R2_Y)

# ── Row 3: Project title  ──────────────────────────────────────────────────
PT1_Y = TB_Y + TB_H * 0.90 - TH_TITLE / 2
add_text(LAYER_TB,
         "DESIGN OF AN INTEGRATED TRAFFIC CALMING SYSTEM",
         (TB_X + TB_W / 2, PT1_Y + TH_TITLE * 0.6),
         height=TH_TITLE, halign="CENTER")
add_text(LAYER_TB,
         "FOR ACCIDENT PREVENTION ON URBAN ROADS USING CAD",
         (TB_X + TB_W / 2, PT1_Y - TH_TITLE * 0.6),
         height=TH_TITLE, halign="CENTER")

# ── Row 2: Drawing title  ──────────────────────────────────────────────────
DT_Y  = (R2_Y + R3_Y) / 2 - TH_SUBHEAD / 2
add_text(LAYER_TB,
         "Drawing No. DWG-01   |   Existing Urban Road Corridor  –  Plan View",
         (TB_X + TB_W / 2, DT_Y),
         height=TH_SUBHEAD, halign="CENTER")

# ── Row 1 helper: stacked text in a column ─────────────────────────────────
def tb_col_text(col_x, col_w, items, row_start_y):
    """
    items : list of (label, value) pairs
    Places each pair on its own line, left-aligned with a margin.
    """
    margin = 2_000
    line_h = TH_SMALL * 1.9   # line spacing
    for j, (lbl, val) in enumerate(items):
        y = row_start_y - j * line_h
        add_text(LAYER_TB, f"{lbl}", (col_x + margin, y),
                 height=TH_SMALL, halign="LEFT")
        add_text(LAYER_TB, f"{val}", (col_x + margin + col_w * 0.38, y),
                 height=TH_SMALL, halign="LEFT")

COL_W = TB_W / 3
ROW1_TOP = R2_Y - TH_SMALL * 0.8   # first line just below the R2 divider

# Left column – Project info
tb_col_text(TB_X, COL_W, [
    ("Project :", "BCV755A Road Safety Engineering"),
    ("Title   :", "Traffic Calming System Design"),
    ("Module  :", "Final Year Project  2026"),
    ("Student :", "___________________________"),
    ("Reg. No.:", "___________________________"),
], ROW1_TOP)

# Middle column – Drawing info
tb_col_text(C1_X, COL_W, [
    ("Drawing No. :", "DWG-01"),
    ("Scale       :", "1 : 1000"),
    ("Units       :", "Millimetres  (mm)"),
    ("Sheet Size  :", "A1 / A0"),
    ("Drawn by    :", "_______________"),
], ROW1_TOP)

# Right column – Revision / approval
tb_col_text(C2_X, COL_W, [
    ("Revision :", "A  –  Initial Issue"),
    ("Date     :", "November  2026"),
    ("Status   :", "EXISTING CONDITIONS"),
    ("Checked  :", "_______________"),
    ("Approved :", "_______________"),
], ROW1_TOP)

# ---------------------------------------------------------------------------
# 14.  Save output as v2 DXF  (original file is NOT touched)
# ---------------------------------------------------------------------------
SCRIPT_DIR   = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
OUTPUT_DIR   = os.path.join(PROJECT_ROOT, "drawings")
OUTPUT_FILE  = os.path.join(OUTPUT_DIR, "01_existing_urban_road_v2.dxf")

os.makedirs(OUTPUT_DIR, exist_ok=True)
doc.saveas(OUTPUT_FILE)

# Verification
if os.path.isfile(OUTPUT_FILE):
    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"[OK]  DXF saved successfully.")
    print(f"      Path : {OUTPUT_FILE}")
    print(f"      Size : {size_kb:.1f} KB")
else:
    print("[ERROR] File was NOT created.  Check permissions.")
    sys.exit(1)
