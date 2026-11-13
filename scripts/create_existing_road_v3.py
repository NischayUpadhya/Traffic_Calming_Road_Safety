"""
=============================================================================
  create_existing_road_v3.py
  BCV755A Road Safety Engineering – Final Year Project
  Drawing : 01_existing_urban_road_v3.dxf
  Description : Existing Urban Road Corridor – Plan View  (v3 CORRECTED)
  Units   : MILLIMETRES  (geometry at 1:1 scale)
  Plot scale  : 1:1000  (A3 landscape sheet, 420 mm × 297 mm)

  ANNOTATION SCALING RULE
  ───────────────────────
  Model-space text height = desired plotted height (mm) × SCALE (1000)

  Plotted targets
  ───────────────
   1.8 mm → 1800 mm   TH_TINY   – dense title-block fields
   2.0 mm → 2000 mm   TH_SMALL  – small notes, CL tag
   2.5 mm → 2500 mm   TH_NORMAL – general annotation, dim text
   3.5 mm → 3500 mm   TH_SUB    – legend heading, lane labels
   4.0 mm → 4000 mm   TH_HEAD   – drawing heading, TB title lines
   5.0 mm → 5000 mm   TH_LARGE  – main road heading above plan

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
  250 000 –287 000  : Top margin

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
# 1.  Plot-scale factor and text-height constants
# ---------------------------------------------------------------------------
SCALE = 1000  # 1 : 1000

TH_TINY   = int(1.8 * SCALE)   # 1800 mm – dense TB fields
TH_SMALL  = int(2.0 * SCALE)   # 2000 mm – small notes
TH_NORMAL = int(2.5 * SCALE)   # 2500 mm – general annotation / dim text
TH_SUB    = int(3.5 * SCALE)   # 3500 mm – sub-headings, lane labels
TH_HEAD   = int(4.0 * SCALE)   # 4000 mm – drawing heading, TB title rows
TH_LARGE  = int(5.0 * SCALE)   # 5000 mm – main road heading

# ---------------------------------------------------------------------------
# 2.  Road geometry constants  (millimetres, 1 : 1 — preserved from v1/v2)
# ---------------------------------------------------------------------------
ROAD_LENGTH      = 200_000
CARRIAGEWAY_W    =   7_000   # = 2 × 3 500
LANE_W           =   3_500
FOOTPATH_W       =   2_000
TOTAL_CORRIDOR_W =  11_000   # 2 000 + 7 000 + 2 000

# Road corridor anchor (bottom-left of lower footpath)
X0        = 70_000
Y_BOT_FP  = 180_000

# Derived road Y-coordinates
Y_LOW_KERB = Y_BOT_FP  + FOOTPATH_W        # 182 000
Y_LANE_DIV = Y_LOW_KERB + LANE_W           # 185 500 (centreline / lane divider)
Y_UPP_KERB = Y_LOW_KERB + CARRIAGEWAY_W    # 189 000
Y_TOP_FP   = Y_BOT_FP  + TOTAL_CORRIDOR_W  # 191 000

X_END   = X0 + ROAD_LENGTH   # 270 000
MID_X   = (X0 + X_END) / 2   # 170 000

MID_Y_L1    = (Y_LOW_KERB + Y_LANE_DIV) / 2  # 183 750
MID_Y_L2    = (Y_LANE_DIV + Y_UPP_KERB) / 2  # 187 250

# ---------------------------------------------------------------------------
# 3.  DXF document
# ---------------------------------------------------------------------------
doc = ezdxf.new(dxfversion="R2010")
doc.header["$INSUNITS"] = 4   # mm
doc.header["$LUNITS"]   = 2
doc.header["$LUPREC"]   = 0

ezdxf.setup_linetypes(doc)    # DASHED, CENTER, CONTINUOUS …
msp = doc.modelspace()

# ---------------------------------------------------------------------------
# 4.  Layers  (seven layers as required)
# ---------------------------------------------------------------------------
LAYER_ROAD  = "ROAD"
LAYER_LANE  = "LANE_MARKINGS"
LAYER_FP    = "FOOTPATH"
LAYER_DIM   = "DIMENSIONS"
LAYER_TEXT  = "TEXT"
LAYER_TB    = "TITLE_BLOCK"
LAYER_LEG   = "LEGEND"

LAYER_SPEC = [
    # (name,        ACI colour,     linetype)
    (LAYER_ROAD,  colors.CYAN,    "CONTINUOUS"),
    (LAYER_LANE,  colors.YELLOW,  "CENTER"),
    (LAYER_FP,    7,              "CONTINUOUS"),   # 7 = white / black
    (LAYER_DIM,   colors.RED,     "CONTINUOUS"),
    (LAYER_TEXT,  colors.WHITE,   "CONTINUOUS"),
    (LAYER_TB,    colors.BLUE,    "CONTINUOUS"),
    (LAYER_LEG,   colors.MAGENTA, "CONTINUOUS"),
]
for lname, lcol, llt in LAYER_SPEC:
    if doc.layers.has_entry(lname):
        lyr = doc.layers.get(lname)
        lyr.dxf.color    = lcol
        lyr.dxf.linetype = llt
    else:
        doc.layers.add(lname, dxfattribs={"color": lcol, "linetype": llt})

# ---------------------------------------------------------------------------
# 5.  Drawing helpers
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
    """Add a DXF TEXT entity with optional alignment."""
    amap = {
        "LEFT":   TextEntityAlignment.LEFT,
        "CENTER": TextEntityAlignment.CENTER,
        "RIGHT":  TextEntityAlignment.RIGHT,
        "MIDDLE": TextEntityAlignment.MIDDLE_CENTER,
    }
    t = msp.add_text(text, height=height, rotation=rotation,
                     dxfattribs={"layer": layer})
    t.set_placement(insert, align=amap.get(halign, TextEntityAlignment.LEFT))

def rect(layer, x, y, w, h):
    """Draw a closed rectangle."""
    msp.add_lwpolyline(
        [(x, y), (x+w, y), (x+w, y+h), (x, y+h)],
        close=True, dxfattribs={"layer": layer},
    )

# ---------------------------------------------------------------------------
# 6.  Sheet border  (A3 landscape: 420 × 297 mm plotted)
# ---------------------------------------------------------------------------
SHEET_W = 420_000
SHEET_H = 297_000
BORDER  =  10_000   # 10 mm inset border

# Outer trim mark (very thin, on TB layer)
rect(LAYER_TB, 0, 0, SHEET_W, SHEET_H)
# Inner drawing border
rect(LAYER_TB,
     BORDER, BORDER,
     SHEET_W - 2*BORDER, SHEET_H - 2*BORDER)

# ---------------------------------------------------------------------------
# 7.  ROAD geometry  (ROAD layer)
# ---------------------------------------------------------------------------
# Outer corridor boundary
hline(LAYER_ROAD, X0, X_END, Y_BOT_FP)   # bottom of lower footpath
hline(LAYER_ROAD, X0, X_END, Y_TOP_FP)   # top of upper footpath
vline(LAYER_ROAD, X0,    Y_BOT_FP, Y_TOP_FP)   # left end cap
vline(LAYER_ROAD, X_END, Y_BOT_FP, Y_TOP_FP)   # right end cap

# Kerb lines (footpath / carriageway boundary)
hline(LAYER_ROAD, X0, X_END, Y_LOW_KERB)   # lower kerb
hline(LAYER_ROAD, X0, X_END, Y_UPP_KERB)   # upper kerb

# ---------------------------------------------------------------------------
# 8.  FOOTPATH hatch  (FOOTPATH layer)
# ---------------------------------------------------------------------------
# Diagonal hatch lines every 5 m within each footpath strip
HATCH_SPACING = 5_000
for xi in range(X0, X_END, HATCH_SPACING):
    # Lower footpath: bottom-left → top-right diagonal
    msp.add_line((xi, Y_BOT_FP), (xi + FOOTPATH_W, Y_LOW_KERB),
                 dxfattribs={"layer": LAYER_FP})
    # Upper footpath: bottom-left → top-right diagonal
    msp.add_line((xi, Y_UPP_KERB), (xi + FOOTPATH_W, Y_TOP_FP),
                 dxfattribs={"layer": LAYER_FP})

# Reinforce footpath outer edges on FP layer
hline(LAYER_FP, X0, X_END, Y_BOT_FP)
hline(LAYER_FP, X0, X_END, Y_TOP_FP)

# ---------------------------------------------------------------------------
# 9.  LANE MARKINGS  (LANE_MARKINGS layer)
# ---------------------------------------------------------------------------
# Lane centreline / divider (CENTER linetype = long-dash-dot)
hline(LAYER_LANE, X0, X_END, Y_LANE_DIV, "DASHED")

# Direction arrows: spaced every 20 m.
# Start at X0+35 000 to leave a clear zone at the left for lane labels.
ARROW_SPACING  = 20_000   # 20 m spacing
ARROW_LEN      =  4_000   # 4 m shaft (4 mm plotted)
ARROW_HEAD_LEN =  1_500   # arrowhead leg
ARROW_HEAD_W   =    800   # arrowhead half-width

for xi in range(int(X0 + 35_000), int(X_END - 5_000), ARROW_SPACING):
    # Lane 1 – Southbound (bottom lane) → arrow pointing ←
    sb_y     = MID_Y_L1
    s_start  = (xi + ARROW_LEN / 2, sb_y)
    s_end    = (xi - ARROW_LEN / 2, sb_y)
    msp.add_line(s_start, s_end,
                 dxfattribs={"layer": LAYER_LANE})
    msp.add_line(s_end,
                 (s_end[0] + ARROW_HEAD_LEN, sb_y + ARROW_HEAD_W),
                 dxfattribs={"layer": LAYER_LANE})
    msp.add_line(s_end,
                 (s_end[0] + ARROW_HEAD_LEN, sb_y - ARROW_HEAD_W),
                 dxfattribs={"layer": LAYER_LANE})

    # Lane 2 – Northbound (top lane) → arrow pointing →
    nb_y     = MID_Y_L2
    n_start  = (xi - ARROW_LEN / 2, nb_y)
    n_end    = (xi + ARROW_LEN / 2, nb_y)
    msp.add_line(n_start, n_end,
                 dxfattribs={"layer": LAYER_LANE})
    msp.add_line(n_end,
                 (n_end[0] - ARROW_HEAD_LEN, nb_y + ARROW_HEAD_W),
                 dxfattribs={"layer": LAYER_LANE})
    msp.add_line(n_end,
                 (n_end[0] - ARROW_HEAD_LEN, nb_y - ARROW_HEAD_W),
                 dxfattribs={"layer": LAYER_LANE})

# ---------------------------------------------------------------------------
# 10.  DIMENSIONS  (DIMENSIONS layer)
#      dimtxt = TH_NORMAL (2500 mm) = 2.5 mm plotted at 1:1000
# ---------------------------------------------------------------------------
doc.dimstyles.duplicate_entry("Standard", "ROAD_DIM_V3")
rd = doc.dimstyles.get("ROAD_DIM_V3")
rd.dxf.dimtxt = TH_NORMAL   # 2500 mm dimension-number text height
rd.dxf.dimasz = 2_000        # arrow size (2 mm plotted)
rd.dxf.dimexo = 1_500        # extension-line offset from reference point
rd.dxf.dimexe = 2_500        # extension-line overshoot past dim line
rd.dxf.dimgap = 1_000        # gap between dim line and text
DS = "ROAD_DIM_V3"

# ── Horizontal dim: road LENGTH (below road, dim-line at Y=160 000) ────────
# (road bottom at 180 000; dim base 20 mm below → 160 000)
dim_len = msp.add_linear_dim(
    base = (MID_X, 160_000),
    p1   = (X0,    Y_BOT_FP),
    p2   = (X_END, Y_BOT_FP),
    dimstyle   = DS,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_len.set_text("200 000 mm  (200 m)")
dim_len.render()

# ── Vertical dims: right of road ───────────────────────────────────────────
# Stack 1: total corridor width  (base X = 290 000)
dim_total = msp.add_linear_dim(
    base = (290_000, Y0 := 0),
    p1   = (X_END, Y_BOT_FP),
    p2   = (X_END, Y_TOP_FP),
    angle      = 90,
    dimstyle   = DS,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_total.set_text("11 000 mm  (Total Width)")
dim_total.render()

# Stack 2: carriageway width  (base X = 310 000)
dim_cwy = msp.add_linear_dim(
    base = (310_000, 0),
    p1   = (X_END, Y_LOW_KERB),
    p2   = (X_END, Y_UPP_KERB),
    angle      = 90,
    dimstyle   = DS,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_cwy.set_text("7 000 mm  (Carriageway)")
dim_cwy.render()

# Stack 3: footpath width  (base X = 330 000)
dim_fp = msp.add_linear_dim(
    base = (330_000, 0),
    p1   = (X_END, Y_BOT_FP),
    p2   = (X_END, Y_LOW_KERB),
    angle      = 90,
    dimstyle   = DS,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_fp.set_text("2 000 mm  (Footpath)")
dim_fp.render()

# ── Vertical dims: left of road ────────────────────────────────────────────
# Stack 1: Lane 1 width  (base X = 55 000)
dim_l1 = msp.add_linear_dim(
    base = (55_000, 0),
    p1   = (X0, Y_LOW_KERB),
    p2   = (X0, Y_LANE_DIV),
    angle      = 90,
    dimstyle   = DS,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_l1.set_text("3 500 mm  (Lane 1)")
dim_l1.render()

# Stack 2: Lane 2 width  (base X = 35 000)
dim_l2 = msp.add_linear_dim(
    base = (35_000, 0),
    p1   = (X0, Y_LANE_DIV),
    p2   = (X0, Y_UPP_KERB),
    angle      = 90,
    dimstyle   = DS,
    dxfattribs = {"layer": LAYER_DIM},
)
dim_l2.set_text("3 500 mm  (Lane 2)")
dim_l2.render()

# ---------------------------------------------------------------------------
# 11.  ROAD ANNOTATIONS  (TEXT layer)
#
#  Zone layout (above road, bottom to top):
#    191 000  : Y_TOP_FP   (road top edge)
#    193 000  : FP-top external callout leader start
#    193 500  : FP-top label baseline   (height 2000, top 195 500)
#    198 000  : scale note baseline     (height 2000, top 200 000)
#    203 000  : drawing heading baseline (height 5000, top 208 000)
#    220 000  : north arrow centre
#
#  Zone layout (below road, top to bottom):
#    180 000  : Y_BOT_FP  (road bottom edge)
#    174 000  : FP-bot external callout label baseline (height 2000, top 176 000)
#    168 000  : (clear gap above road-length dim text)
#    160 000  : road-length dim line
#    157 500  : dim text top  (160 000 − 2500 mm text, top ~162 500)
# ---------------------------------------------------------------------------

# ── 11a. Road heading (above road, in its own clear zone) ──────────────────
#         Placed 12 mm plotted above road top (Y_TOP_FP = 191 000)
add_text(LAYER_TEXT,
         "EXISTING TWO-WAY URBAN ROAD CORRIDOR  –  PLAN VIEW",
         (MID_X, 203_000),
         height=TH_LARGE, halign="CENTER")

# ── 11b. Scale / units note (just above road, below heading) ───────────────
add_text(LAYER_TEXT,
         "SCALE : 1:1000     UNITS : MILLIMETRES     SHEET : A3 LANDSCAPE",
         (MID_X, 198_000),
         height=TH_SMALL, halign="CENTER")

# ── 11c. Lane labels  ──────────────────────────────────────────────────────
#   Placed in the clear 35 m zone at the LEFT end of the road (X0 to X0+33 000),
#   before the first direction arrow (which starts at X0+35 000 = 105 000).
#   Both labels are LEFT-ALIGNED from X=72 000 (2 mm inside the road boundary).
#   Lane 1 (bottom): baseline centred in Lane 1 height
#   Lane 2 (top):    baseline centred in Lane 2 height

L1_LBL_X = X0 + 2_000   # 72 000 — left of first arrow, inside road boundary
L2_LBL_X = X0 + 2_000

# Lane 1 centre Y: (Y_LOW_KERB + Y_LANE_DIV) / 2 = 183 750
#  → baseline = 183 750 − TH_SUB/2 = 183 750 − 1 750 = 182 000
add_text(LAYER_TEXT,
         "LANE 1  –  SOUTHBOUND  (3.5 m)",
         (L1_LBL_X, int(MID_Y_L1 - TH_SUB / 2)),
         height=TH_SUB, halign="LEFT")

# Lane 2 centre Y: (Y_LANE_DIV + Y_UPP_KERB) / 2 = 187 250
#  → baseline = 187 250 − 1 750 = 185 500
add_text(LAYER_TEXT,
         "LANE 2  –  NORTHBOUND  (3.5 m)",
         (L2_LBL_X, int(MID_Y_L2 - TH_SUB / 2)),
         height=TH_SUB, halign="LEFT")

# ── 11d. Centreline tag  ───────────────────────────────────────────────────
#   Short "C/L" placed just to the LEFT of the road boundary at the centreline
#   height, right-aligned so it does not intrude into the lane area.
add_text(LAYER_TEXT, "C/L",
         (X0 - 1_500, Y_LANE_DIV + 400),
         height=TH_SMALL, halign="RIGHT")

# Mirror tag at right end of road (outside road boundary, left-aligned)
add_text(LAYER_TEXT, "C/L",
         (X_END + 1_500, Y_LANE_DIV + 400),
         height=TH_SMALL, halign="LEFT")

# ── 11e. Footpath external callouts  ───────────────────────────────────────
#   The 2 000 mm footpath strip is too narrow for internal text at any
#   readable size.  External callout labels are placed outside the road with
#   a short leader line pointing to the strip.

# ---- TOP footpath callout (label above Y_TOP_FP) ----
FP_TOP_CALLOUT_X = MID_X            # centred horizontally on road
FP_TOP_LBL_Y     = 193_500          # baseline (2.5 mm above road top)
# Leader: short vertical tick from label down to the footpath top edge
msp.add_line(
    (FP_TOP_CALLOUT_X, FP_TOP_LBL_Y - 400),
    (FP_TOP_CALLOUT_X, Y_TOP_FP),
    dxfattribs={"layer": LAYER_TEXT},
)
# Tick at the footpath edge
msp.add_line(
    (FP_TOP_CALLOUT_X - 1_500, Y_TOP_FP),
    (FP_TOP_CALLOUT_X + 1_500, Y_TOP_FP),
    dxfattribs={"layer": LAYER_TEXT},
)
add_text(LAYER_TEXT, "FOOTPATH  (W = 2.0 m)",
         (FP_TOP_CALLOUT_X, FP_TOP_LBL_Y),
         height=TH_SMALL, halign="CENTER")

# ---- BOTTOM footpath callout (label below Y_BOT_FP) ----
FP_BOT_CALLOUT_X = MID_X
FP_BOT_LBL_Y     = 174_000          # baseline (6 mm below road bottom;
                                     # sits between road edge and dim line)
# Leader: short vertical tick from label up to the footpath bottom edge
msp.add_line(
    (FP_BOT_CALLOUT_X, FP_BOT_LBL_Y + TH_SMALL + 400),
    (FP_BOT_CALLOUT_X, Y_BOT_FP),
    dxfattribs={"layer": LAYER_TEXT},
)
msp.add_line(
    (FP_BOT_CALLOUT_X - 1_500, Y_BOT_FP),
    (FP_BOT_CALLOUT_X + 1_500, Y_BOT_FP),
    dxfattribs={"layer": LAYER_TEXT},
)
add_text(LAYER_TEXT, "FOOTPATH  (W = 2.0 m)",
         (FP_BOT_CALLOUT_X, FP_BOT_LBL_Y),
         height=TH_SMALL, halign="CENTER")

# ---------------------------------------------------------------------------
# 12.  NORTH ARROW  (TEXT layer)
#      Placed in the upper-right quadrant, well clear of all dims and labels.
#      Centre: X=370 000, Y=228 000  –  well outside road and dim columns.
# ---------------------------------------------------------------------------
NA_X    = 370_000
NA_Y    = 228_000
NA_SIZE = 7_000     # 7 mm plotted half-shaft

# Shaft (vertical, points North)
msp.add_line((NA_X, NA_Y - NA_SIZE), (NA_X, NA_Y + NA_SIZE),
             dxfattribs={"layer": LAYER_TEXT})
# Arrowhead wings (pointing up)
msp.add_line((NA_X, NA_Y + NA_SIZE),
             (NA_X - 1_500, NA_Y + NA_SIZE - 3_500),
             dxfattribs={"layer": LAYER_TEXT})
msp.add_line((NA_X, NA_Y + NA_SIZE),
             (NA_X + 1_500, NA_Y + NA_SIZE - 3_500),
             dxfattribs={"layer": LAYER_TEXT})
# Closed filled triangle effect (third line)
msp.add_line((NA_X - 1_500, NA_Y + NA_SIZE - 3_500),
             (NA_X + 1_500, NA_Y + NA_SIZE - 3_500),
             dxfattribs={"layer": LAYER_TEXT})
# Circle at base of arrow
msp.add_circle((NA_X, NA_Y - NA_SIZE), radius=1_200,
               dxfattribs={"layer": LAYER_TEXT})
# "N" label (above arrow tip)
add_text(LAYER_TEXT, "N",
         (NA_X, NA_Y + NA_SIZE + 1_500),
         height=TH_HEAD, halign="CENTER")
# "NORTH" annotation below circle
add_text(LAYER_TEXT, "NORTH",
         (NA_X, NA_Y - NA_SIZE - TH_SMALL - 1_000),
         height=TH_SMALL, halign="CENTER")

# ---------------------------------------------------------------------------
# 13.  LEGEND PANEL  (LEGEND layer for border; TEXT layer for content)
#      Positioned in the zone Y=80 000 → 135 000, X=10 000 → 420−10=410 000
#      We use left half for content (X=10 000 → 280 000) and right for notes.
# ---------------------------------------------------------------------------
LEG_X     = BORDER               # 10 000
LEG_Y     = 80_000
LEG_W     = SHEET_W - 2*BORDER   # 400 000  (full inner width)
LEG_H     = 55_000
LEG_X_END = LEG_X + LEG_W

# Outer border of legend panel
rect(LAYER_LEG, LEG_X, LEG_Y, LEG_W, LEG_H)

# Heading "LEGEND" at top-left of legend panel
LEG_HEAD_Y = LEG_Y + LEG_H - 3_000   # baseline of heading
add_text(LAYER_LEG, "LEGEND",
         (LEG_X + 2_000, LEG_HEAD_Y),
         height=TH_HEAD)

# Horizontal divider below heading
hline(LAYER_LEG, LEG_X, LEG_X_END, LEG_HEAD_Y - 1_000)

# Legend items
# (layer name, colour description, linetype description, example-swatch layer)
LEG_ITEMS = [
    (LAYER_ROAD,  "ROAD",          "Road & carriageway boundaries (Cyan, Continuous)"),
    (LAYER_LANE,  "LANE_MARKINGS", "Lane centreline / divider, direction arrows (Yellow, Dashed)"),
    (LAYER_FP,    "FOOTPATH",      "Footpath strips with diagonal hatch (White, Continuous)"),
    (LAYER_DIM,   "DIMENSIONS",    "Dimension lines and callout text (Red, Continuous)"),
    (LAYER_TEXT,  "TEXT",          "Annotation, labels, north arrow, callouts (White, Continuous)"),
    (LAYER_TB,    "TITLE_BLOCK",   "Title block border, sheet border (Blue, Continuous)"),
    (LAYER_LEG,   "LEGEND",        "Legend panel border and headings (Magenta, Continuous)"),
]

SWATCH_LEN = 8_000           # swatch line length (8 mm plotted)
LEG_ROW_H  = int(TH_SMALL * 2.0)  # row spacing (4 000 mm)

# First item starts 2 rows below the heading divider
LEG_ROW1_Y = LEG_HEAD_Y - 1_000 - 1_500  # baseline of first item

for i, (lyr, lyr_name, description) in enumerate(LEG_ITEMS):
    row_y = LEG_ROW1_Y - i * LEG_ROW_H

    # Swatch line in item's own layer colour
    msp.add_line(
        (LEG_X + 2_000, row_y + TH_SMALL * 0.35),
        (LEG_X + 2_000 + SWATCH_LEN, row_y + TH_SMALL * 0.35),
        dxfattribs={"layer": lyr},
    )
    # Layer name (bold substitute: same text twice offset by 50 mm — omit for CAD)
    add_text(LAYER_LEG, lyr_name,
             (LEG_X + 2_000 + SWATCH_LEN + 1_500, row_y),
             height=TH_SMALL)
    # Description
    add_text(LAYER_LEG, description,
             (LEG_X + 2_000 + SWATCH_LEN + 55_000, row_y),
             height=TH_SMALL)

# ---------------------------------------------------------------------------
# 14.  TITLE BLOCK  (TITLE_BLOCK layer)
#
#  Overall: X = 10 000 → 410 000  (W = 400 000)
#           Y = 10 000 →  75 000  (H =  65 000)
#
#  Row structure (bottom → top):
#   Row A – field data   (60% of H = 39 000): Y=10 000 → 49 000
#   Row B – drawing title (15% of H =  9 750): Y=49 000 → 58 750
#   Row C – project title (25% of H = 16 250): Y=58 750 → 75 000
#
#  Column structure (Row A only):
#   Col 1: X=10 000  → 143 333  (project info)
#   Col 2: X=143 333 → 276 667  (drawing info)
#   Col 3: X=276 667 → 410 000  (revision / approval)
# ---------------------------------------------------------------------------
TB_X   = BORDER        # 10 000
TB_Y   = BORDER        # 10 000
TB_W   = SHEET_W - 2*BORDER   # 400 000
TB_H   = 65_000
TB_END = TB_X + TB_W  # 410 000

# Row boundaries
TB_ROW_A_BOT = TB_Y                        # 10 000
TB_ROW_A_TOP = TB_Y + int(TB_H * 0.60)    # 49 000
TB_ROW_B_BOT = TB_ROW_A_TOP               # 49 000
TB_ROW_B_TOP = TB_Y + int(TB_H * 0.75)    # 58 750
TB_ROW_C_BOT = TB_ROW_B_TOP               # 58 750
TB_ROW_C_TOP = TB_Y + TB_H                # 75 000

# Column boundaries (apply to Row A only)
TB_COL1_X = TB_X                          # 10 000
TB_COL2_X = TB_X + TB_W // 3             # 143 333
TB_COL3_X = TB_X + 2 * (TB_W // 3)      # 276 667

# --- Outer border and row dividers ---
rect(LAYER_TB, TB_X, TB_Y, TB_W, TB_H)
hline(LAYER_TB, TB_X, TB_END, TB_ROW_A_TOP)   # Row A / B divider
hline(LAYER_TB, TB_X, TB_END, TB_ROW_B_TOP)   # Row B / C divider
# Column dividers (Row A only)
vline(LAYER_TB, TB_COL2_X, TB_ROW_A_BOT, TB_ROW_A_TOP)
vline(LAYER_TB, TB_COL3_X, TB_ROW_A_BOT, TB_ROW_A_TOP)

# ── Row C: Project title (top band) ────────────────────────────────────────
# Two title lines centred in the band.  TH_HEAD = 4 000 mm → 4 mm plotted.
ROW_C_MID = (TB_ROW_C_BOT + TB_ROW_C_TOP) / 2   # 66 875
ROW_C_LINE_H = TH_HEAD * 1.4   # line-to-line spacing = 5 600 mm

add_text(LAYER_TB,
         "DESIGN OF AN INTEGRATED TRAFFIC CALMING SYSTEM",
         (TB_X + TB_W / 2, ROW_C_MID + ROW_C_LINE_H / 2 - TH_HEAD * 0.4),
         height=TH_HEAD, halign="CENTER")
add_text(LAYER_TB,
         "FOR ACCIDENT PREVENTION ON URBAN ROADS USING CAD",
         (TB_X + TB_W / 2, ROW_C_MID - ROW_C_LINE_H / 2 - TH_HEAD * 0.4),
         height=TH_HEAD, halign="CENTER")

# ── Row B: Drawing title (mid band) ────────────────────────────────────────
ROW_B_MID = (TB_ROW_B_BOT + TB_ROW_B_TOP) / 2   # 53 875
add_text(LAYER_TB,
         "DRAWING NO. DWG-01   |   Existing Urban Road Corridor  –  Plan View"
         "   |   Sheet 1 of 1",
         (TB_X + TB_W / 2, int(ROW_B_MID - TH_NORMAL * 0.5)),
         height=TH_NORMAL, halign="CENTER")

# ── Row A: Field data (bottom band, 3 columns) ─────────────────────────────
# Helper: stack labelled fields in a column.
# Each field has a LABEL (left part) and a VALUE (right part).
# Fields are stacked from top of Row A downward.

FIELD_H    = TH_TINY         # 1 800 mm field text
FIELD_LINE = int(FIELD_H * 2.1)   # line spacing: 3 780 mm ≈ 3 800 mm
FIELD_TOP  = TB_ROW_A_TOP - 2_000   # first row baseline
MARGIN_L   = 1_500   # left margin inside each column

def tb_field(col_x, row_idx, label, value):
    """Draw one label : value row inside a title-block column."""
    y = FIELD_TOP - row_idx * FIELD_LINE
    add_text(LAYER_TB, label,
             (col_x + MARGIN_L, y), height=FIELD_H)
    add_text(LAYER_TB, value,
             (col_x + MARGIN_L + 35_000, y), height=FIELD_H)

# Column 1 – Project information
COL1_FIELDS = [
    ("Project  :", "BCV755A Road Safety Engineering"),
    ("Title    :", "Traffic Calming System Design"),
    ("Module   :", "Road Safety Engineering"),
    ("Institution:", "_______________________"),
    ("Student  :", "_______________________"),
    ("Reg. No. :", "_______________________"),
    ("Supervisor:", "_______________________"),
]
for idx, (lbl, val) in enumerate(COL1_FIELDS):
    tb_field(TB_COL1_X, idx, lbl, val)

# Column 2 – Drawing details
COL2_FIELDS = [
    ("Drawing No. :", "DWG-01"),
    ("Title       :", "Existing Road Corridor"),
    ("Scale       :", "1 : 1000"),
    ("Units       :", "Millimetres  (mm)"),
    ("Sheet Size  :", "A3 Landscape"),
    ("Drawn by    :", "_______________"),
    ("Date Drawn  :", "_______________"),
]
for idx, (lbl, val) in enumerate(COL2_FIELDS):
    tb_field(TB_COL2_X, idx, lbl, val)

# Column 3 – Revision and approval
COL3_FIELDS = [
    ("Revision  :", "A  –  Initial Issue"),
    ("Status    :", "EXISTING CONDITIONS"),
    ("Date      :", "November  2026"),
    ("Checked by:", "_______________"),
    ("Approved  :", "_______________"),
    ("File Ref. :", "DWG-01-A-EX-ROAD"),
    ("CAD Ref.  :", "BCV755A-DWG-01"),
]
for idx, (lbl, val) in enumerate(COL3_FIELDS):
    tb_field(TB_COL3_X, idx, lbl, val)

# ---------------------------------------------------------------------------
# 15.  Save v3 DXF  (originals v1 and v2 are NOT touched)
# ---------------------------------------------------------------------------
SCRIPT_DIR   = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
OUTPUT_DIR   = os.path.join(PROJECT_ROOT, "drawings")
OUTPUT_FILE  = os.path.join(OUTPUT_DIR, "01_existing_urban_road_v3.dxf")

os.makedirs(OUTPUT_DIR, exist_ok=True)
doc.saveas(OUTPUT_FILE)

# Verification
if os.path.isfile(OUTPUT_FILE):
    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"[OK]  DXF v3 saved successfully.")
    print(f"      Path : {OUTPUT_FILE}")
    print(f"      Size : {size_kb:.1f} KB")
else:
    print("[ERROR] File was NOT created.  Check write permissions.")
    sys.exit(1)
