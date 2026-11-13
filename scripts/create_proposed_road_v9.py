"""
create_proposed_road_v9.py
BCV755A Road Safety Engineering – Final Year Project
Drawing : 02_proposed_traffic_calming_road_v9.dxf
Description : Final presentation clean‑up of enlarged crossing detail (Version 9)
Units   : MILLIMETRES  (geometry at 1:1 scale for main plan, detail enlarged to 1:100)
Plot scale  : 1:1000  (A3 landscape sheet)
"""

# ---------------------------------------------------------------------------
# 0. Imports and dependency check
# ---------------------------------------------------------------------------
import os
import sys
import math

try:
    import ezdxf
    from ezdxf import colors
    from ezdxf.enums import TextEntityAlignment
except ModuleNotFoundError:
    print("ezdxf is not installed. Run:   pip install ezdxf")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 1. Plot‑scale factor and text‑height constants (main‑plan 1:1000)
# ---------------------------------------------------------------------------
SCALE = 1000  # main‑plan 1:1000

TH_TINY   = int(1.8 * SCALE)
TH_SMALL  = int(2.0 * SCALE)
TH_NORMAL = int(2.5 * SCALE)
TH_SUB    = int(3.5 * SCALE)
TH_HEAD   = int(4.0 * SCALE)
TH_LARGE  = int(5.0 * SCALE)

# ---------------------------------------------------------------------------
# 2. Road geometry constants (unchanged, 1:1 mm)
# ---------------------------------------------------------------------------
ROAD_LENGTH      = 200_000
CARRIAGEWAY_W    =   7_000
LANE_W           =   3_500
FOOTPATH_W       =   2_000
TOTAL_CORRIDOR_W =  11_000

X0        = 70_000
Y_BOT_FP  = 180_000
Y_LOW_KERB = Y_BOT_FP + FOOTPATH_W
Y_LANE_DIV = Y_LOW_KERB + LANE_W
Y_UPP_KERB = Y_LOW_KERB + CARRIAGEWAY_W
Y_TOP_FP   = Y_BOT_FP + TOTAL_CORRIDOR_W
X_END   = X0 + ROAD_LENGTH
MID_X   = (X0 + X_END) / 2
MID_Y_L1 = (Y_LOW_KERB + Y_LANE_DIV) / 2
MID_Y_L2 = (Y_LANE_DIV + Y_UPP_KERB) / 2

# ---------------------------------------------------------------------------
# 3. DXF document setup
# ---------------------------------------------------------------------------

doc = ezdxf.new(dxfversion="R2010")
doc.header["$INSUNITS"] = 4   # mm

ezdxf.setup_linetypes(doc)

msp = doc.modelspace()

# ---------------------------------------------------------------------------
# 4. Layers (same as previous versions)
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
    (LAYER_SIGNS,           colors.YELLOW,  "CONTINUOUS"),
]
for lname, lcol, llt in LAYER_SPEC:
    if doc.layers.has_entry(lname):
        lyr = doc.layers.get(lname)
        lyr.dxf.color    = lcol
        lyr.dxf.linetype = llt
    else:
        doc.layers.add(lname, dxfattribs={"color": lcol, "linetype": llt})

# ---------------------------------------------------------------------------
# 5. Helper drawing functions
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
# 6. Sheet border (A3 landscape)
# ---------------------------------------------------------------------------
SHEET_W = 420_000
SHEET_H = 297_000
BORDER  = 10_000

rect("TITLE_BLOCK", 0, 0, SHEET_W, SHEET_H)
rect("TITLE_BLOCK", BORDER, BORDER, SHEET_W - 2 * BORDER, SHEET_H - 2 * BORDER)

# ---------------------------------------------------------------------------
# 7. ROAD geometry (unchanged – same as previous versions)
# ---------------------------------------------------------------------------
hline(LAYER_ROAD, X0, X_END, Y_BOT_FP)
hline(LAYER_ROAD, X0, X_END, Y_TOP_FP)
vline(LAYER_ROAD, X0, Y_BOT_FP, Y_TOP_FP)
vline(LAYER_ROAD, X_END, Y_BOT_FP, Y_TOP_FP)

hline(LAYER_ROAD, X0, X_END, Y_LOW_KERB)
hline(LAYER_ROAD, X0, X_END, Y_UPP_KERB)

# ---------------------------------------------------------------------------
# 8. FOOTPATH hatch (simplified diagonal lines)
# ---------------------------------------------------------------------------
HATCH_SPACING = 5_000
for xi in range(X0, X_END, HATCH_SPACING):
    msp.add_line((xi, Y_BOT_FP), (xi + FOOTPATH_W, Y_LOW_KERB), dxfattribs={"layer": LAYER_FP})
    msp.add_line((xi, Y_UPP_KERB), (xi + FOOTPATH_W, Y_TOP_FP), dxfattribs={"layer": LAYER_FP})

hline(LAYER_FP, X0, X_END, Y_BOT_FP)
hline(LAYER_FP, X0, X_END, Y_TOP_FP)

# ---------------------------------------------------------------------------
# 9. LANE MARKINGS – directional arrows
# ---------------------------------------------------------------------------
hline(LAYER_LANE, X0, X_END, Y_LANE_DIV, "DASHED")

ARROW_SPACING = 20_000
ARROW_LEN = 4_000
ARROW_HEAD_LEN = 1_500
ARROW_HEAD_W = 800

for xi in range(int(X0 + 35_000), int(X_END - 5_000), ARROW_SPACING):
    # Lane 1 – Southbound (←)
    sb_y = MID_Y_L1
    s_start = (xi + ARROW_LEN / 2, sb_y)
    s_end   = (xi - ARROW_LEN / 2, sb_y)
    msp.add_line(s_start, s_end, dxfattribs={"layer": LAYER_LANE})
    msp.add_line(s_end, (s_end[0] + ARROW_HEAD_LEN, sb_y + ARROW_HEAD_W), dxfattribs={"layer": LAYER_LANE})
    msp.add_line(s_end, (s_end[0] + ARROW_HEAD_LEN, sb_y - ARROW_HEAD_W), dxfattribs={"layer": LAYER_LANE})
    # Lane 2 – Northbound (→)
    nb_y = MID_Y_L2
    n_start = (xi - ARROW_LEN / 2, nb_y)
    n_end   = (xi + ARROW_LEN / 2, nb_y)
    msp.add_line(n_start, n_end, dxfattribs={"layer": LAYER_LANE})
    msp.add_line(n_end, (n_end[0] - ARROW_HEAD_LEN, nb_y + ARROW_HEAD_W), dxfattribs={"layer": LAYER_LANE})
    msp.add_line(n_end, (n_end[0] - ARROW_HEAD_LEN, nb_y - ARROW_HEAD_W), dxfattribs={"layer": LAYER_LANE})

# ---------------------------------------------------------------------------
# 10. DIMENSIONS (custom dimstyle)
# ---------------------------------------------------------------------------

doc.dimstyles.duplicate_entry("Standard", "ROAD_DIM_V3")
rd = doc.dimstyles.get("ROAD_DIM_V3")
rd.dxf.dimtxt = TH_NORMAL
rd.dxf.dimasz = 2_000
rd.dxf.dimexo = 1_500
rd.dxf.dimexe = 2_500
rd.dxf.dimgap = 1_000
DS = "ROAD_DIM_V3"

# Length dimension (main plan)

dim_len = msp.add_linear_dim(
    base=(MID_X, 160_000),
    p1=(X0, Y_BOT_FP),
    p2=(X_END, Y_BOT_FP),
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)

dim_len.set_text("200 000 mm  (200 m)")

dim_len.render()

# Width dimension (right side)

dim_total = msp.add_linear_dim(
    base=(290_000, 0),
    p1=(X_END, Y_BOT_FP),
    p2=(X_END, Y_TOP_FP),
    angle=90,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)

dim_total.set_text("11 000 mm  (Total Width)")

dim_total.render()

# Carriageway width

dim_cwy = msp.add_linear_dim(
    base=(310_000, 0),
    p1=(X_END, Y_LOW_KERB),
    p2=(X_END, Y_UPP_KERB),
    angle=90,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)

dim_cwy.set_text("7 000 mm  (Carriageway)")

dim_cwy.render()

# Footpath width

dim_fp = msp.add_linear_dim(
    base=(330_000, 0),
    p1=(X_END, Y_BOT_FP),
    p2=(X_END, Y_LOW_KERB),
    angle=90,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)

dim_fp.set_text("2 000 mm  (Footpath)")

dim_fp.render()

# Lane widths (left side)

dim_l1 = msp.add_linear_dim(
    base=(55_000, 0),
    p1=(X0, Y_LOW_KERB),
    p2=(X0, Y_LANE_DIV),
    angle=90,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)

dim_l1.set_text("3 500 mm  (Lane 1)")

dim_l1.render()


dim_l2 = msp.add_linear_dim(
    base=(35_000, 0),
    p1=(X0, Y_LANE_DIV),
    p2=(X0, Y_UPP_KERB),
    angle=90,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)

dim_l2.set_text("3 500 mm  (Lane 2)")

dim_l2.render()

# ---------------------------------------------------------------------------
# 11. ROAD ANNOTATIONS – heading, scale note, footpath callouts
# ---------------------------------------------------------------------------
add_text(LAYER_TEXT, "PROPOSED URBAN ROAD WITH INTEGRATED TRAFFIC CALMING MEASURES",
         (MID_X, 203_000), height=TH_LARGE, halign="CENTER")
add_text(LAYER_TEXT, "SCALE : 1:1000     UNITS : MILLIMETRES     SHEET : A3 LANDSCAPE",
         (MID_X, 198_000), height=TH_SMALL, halign="CENTER")

add_text(LAYER_TEXT, "C/L",
         (X0 - 1_500, Y_LANE_DIV + 400), height=TH_SMALL, halign="RIGHT")
add_text(LAYER_TEXT, "C/L",
         (X_END + 1_500, Y_LANE_DIV + 400), height=TH_SMALL, halign="LEFT")

FP_TOP_CALLOUT_X = MID_X
FP_TOP_LBL_Y = 193_500
msp.add_line((FP_TOP_CALLOUT_X, FP_TOP_LBL_Y - 400), (FP_TOP_CALLOUT_X, Y_TOP_FP), dxfattribs={"layer": LAYER_TEXT})
add_text(LAYER_TEXT, "FOOTPATH  (W = 2.0 m)", (FP_TOP_CALLOUT_X, FP_TOP_LBL_Y), height=TH_SMALL, halign="CENTER")

FP_BOT_CALLOUT_X = MID_X
FP_BOT_LBL_Y = 174_000
msp.add_line((FP_BOT_CALLOUT_X, FP_BOT_LBL_Y + TH_SMALL + 400), (FP_BOT_CALLOUT_X, Y_BOT_FP), dxfattribs={"layer": LAYER_TEXT})
add_text(LAYER_TEXT, "FOOTPATH  (W = 2.0 m)", (FP_BOT_CALLOUT_X, FP_BOT_LBL_Y), height=TH_SMALL, halign="CENTER")

# ---------------------------------------------------------------------------
# 12. TRAFFIC CALMING FEATURES – crossing callouts (unchanged)
# ---------------------------------------------------------------------------

def draw_crossing(chainage_mm, label_suffix):
    xc = X0 + chainage_mm
    table_len = 6_000
    table_x0 = xc - table_len / 2
    table_y0 = Y_LOW_KERB
    rect(LAYER_TRAFFIC_CALMING, table_x0, table_y0, table_len, CARRIAGEWAY_W)
    # Zebra stripes – 7 dashed lines
    num_stripes = 7
    stripe_spacing = CARRIAGEWAY_W / (num_stripes + 1)
    for i in range(1, num_stripes + 1):
        y_stripe = Y_LOW_KERB + i * stripe_spacing
        hline(LAYER_TRAFFIC_CALMING, table_x0, table_x0 + table_len, y_stripe, "DASHED")
    # Warning / speed signs (unchanged)
    sign_offset = 3_000
    sign_x = X0 - sign_offset
    sign_y = Y_LOW_KERB + CARRIAGEWAY_W / 2
    rect(LAYER_SIGNS, sign_x - 1_500, sign_y - 1_500, 3_000, 3_000)
    add_text(LAYER_SIGNS, "WARN", (sign_x, sign_y), height=TH_SMALL, halign="CENTER")
    speed_x = xc - 5_000
    speed_y = Y_LOW_KERB + CARRIAGEWAY_W / 2
    rect(LAYER_SIGNS, speed_x - 1_500, speed_y - 1_500, 3_000, 3_000)
    add_text(LAYER_SIGNS, "SPEED 30", (speed_x, speed_y), height=TH_SMALL, halign="CENTER")
    # Reflective studs – simplified
    stud_spacing = 20_000
    num_studs = int(table_len // stud_spacing) + 1
    for i in range(num_studs):
        xs = table_x0 + i * stud_spacing
        msp.add_circle((xs, Y_LOW_KERB), radius=200, dxfattribs={"layer": LAYER_TRAFFIC_CALMING})
        msp.add_circle((xs, Y_UPP_KERB), radius=200, dxfattribs={"layer": LAYER_TRAFFIC_CALMING})
    # Callout placement
    if label_suffix == "A":
        call_y = Y_UPP_KERB + 8_000
    else:
        call_y = Y_LOW_KERB - 8_000
    add_text(LAYER_TEXT, f"CROSSING {label_suffix}", (xc, call_y), height=TH_SUB, halign="CENTER")
    msp.add_line((xc, call_y), (xc, Y_LANE_DIV), dxfattribs={"layer": LAYER_TEXT})

draw_crossing(60_000, "A")
draw_crossing(140_000, "B")

# ---------------------------------------------------------------------------
# 13. NORTH ARROW (upper‑right quadrant)
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
# 14. LEGEND PANEL (lower panel)
# ---------------------------------------------------------------------------
LEG_X = BORDER
LEG_Y = 80_000
LEG_W = SHEET_W - 2 * BORDER
LEG_H = 55_000
rect(LAYER_LEG, LEG_X, LEG_Y, LEG_W, LEG_H)
LEG_HEAD_Y = LEG_Y + LEG_H - 3_000
add_text(LAYER_LEG, "LEGEND", (LEG_X + 2_000, LEG_HEAD_Y), height=TH_HEAD)
hline(LAYER_LEG, LEG_X, LEG_X + LEG_W, LEG_HEAD_Y - 1_000)

LEG_ITEMS = [
    (LAYER_ROAD,            "ROAD",            "Road & carriageway boundaries (Cyan, Continuous)"),
    (LAYER_LANE,            "LANE_MARKINGS",   "Lane centreline / divider, direction arrows (Yellow, Dashed)"),
    (LAYER_FP,              "FOOTPATH",        "Footpath strips (White, Continuous)"),
    (LAYER_TRAFFIC_CALMING, "TRAFFIC_CALMING", "Raised crossings, warning markings, studs"),
    (LAYER_SIGNS,           "SIGNS",           "Warning & speed‑limit signs"),
    (LAYER_DIM,             "DIMENSIONS",      "Dimension lines (Red)"),
    (LAYER_TEXT,            "TEXT",            "Annotations (White)"),
    (LAYER_TB,              "TITLE_BLOCK",     "Title block (Blue)"),
    (LAYER_LEG,             "LEGEND",          "Legend panel (Magenta)"),
]
SWATCH_LEN = 8_000
LEG_ROW_H = int(TH_SMALL * 2.0)
LEG_ROW1_Y = LEG_HEAD_Y - 1_000 - 1_500
for i, (lyr, name, desc) in enumerate(LEG_ITEMS):
    row_y = LEG_ROW1_Y - i * LEG_ROW_H
    msp.add_line((LEG_X + 2_000, row_y + TH_SMALL * 0.35),
                 (LEG_X + 2_000 + SWATCH_LEN, row_y + TH_SMALL * 0.35),
                 dxfattribs={"layer": lyr})
    add_text(LAYER_LEG, name, (LEG_X + 2_000 + SWATCH_LEN + 1_500, row_y), height=TH_SMALL)
    add_text(LAYER_LEG, desc, (LEG_X + 2_000 + SWATCH_LEN + 55_000, row_y), height=TH_SMALL)

# ---------------------------------------------------------------------------
# 15. TITLE BLOCK (bottom panel)
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

# Project title (row C)
ROW_C_MID = (TB_ROW_C_BOT + TB_ROW_C_TOP) / 2
ROW_C_LINE_H = TH_HEAD * 1.4
add_text(LAYER_TB,
         "DESIGN OF AN INTEGRATED TRAFFIC CALMING SYSTEM",
         (TB_X + TB_W / 2, ROW_C_MID + ROW_C_LINE_H / 2 - TH_HEAD * 0.4),
         height=TH_HEAD, halign="CENTER")
add_text(LAYER_TB,
         "FOR ACCIDENT PREVENTION ON URBAN ROADS USING CAD",
         (TB_X + TB_W / 2, ROW_C_MID - ROW_C_LINE_H / 2 - TH_HEAD * 0.4),
         height=TH_HEAD, halign="CENTER")
# Drawing title (row B)
ROW_B_MID = (TB_ROW_B_BOT + TB_ROW_B_TOP) / 2
add_text(LAYER_TB,
         "DRAWING NO. DWG-02   |   Proposed Urban Road with Traffic Calming – Plan View   |   Sheet 1 of 1",
         (TB_X + TB_W / 2, int(ROW_B_MID - TH_NORMAL * 0.5)),
         height=TH_NORMAL, halign="CENTER")
# Fields (row A)
FIELD_H = TH_TINY
FIELD_LINE = int(FIELD_H * 2.1)
FIELD_TOP = TB_ROW_A_TOP - 2_000
MARGIN_L = 1_500

def tb_field(col_x, idx, label, value):
    y = FIELD_TOP - idx * FIELD_LINE
    add_text(LAYER_TB, label, (col_x + MARGIN_L, y), height=FIELD_H)
    add_text(LAYER_TB, value, (col_x + MARGIN_L + 35_000, y), height=FIELD_H)

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

# Conceptual‑design note (row A)
add_text(LAYER_TB,
         "CONCEPTUAL DESIGN – FINAL DIMENSIONS SUBJECT TO SITE SURVEY AND IRC / LOCAL AUTHORITY VERIFICATION",
         (TB_X + TB_W / 2, TB_ROW_A_BOT + 5_000), height=TH_TINY, halign="CENTER")

# ---------------------------------------------------------------------------
# 16. ENLARGED DETAIL – cleaned up 1:100 scale (factor 10 enlargement)
# ---------------------------------------------------------------------------
DETAIL_X0 = 200_000
DETAIL_Y0 = 250_000   # bottom of panel (leaves vertical space for title above)
DETAIL_W  = 220_000
DETAIL_H  = 130_000
rect(LAYER_TEXT, DETAIL_X0, DETAIL_Y0, DETAIL_W, DETAIL_H)

# Title above panel
add_text(LAYER_TEXT, "TYPICAL RAISED PEDESTRIAN CROSSING - PLAN DETAIL",
         (DETAIL_X0 + DETAIL_W/2, DETAIL_Y0 + DETAIL_H + 5_000),
         height=TH_SUB, halign="CENTER")
# Scale note directly below title
add_text(LAYER_TEXT, "CONCEPTUAL SCALE 1:100",
         (DETAIL_X0 + DETAIL_W/2, DETAIL_Y0 + DETAIL_H + 20_000),
         height=TH_SMALL, halign="CENTER")

FACTOR = 10
REAL_FOOTPATH_W = 2_000
REAL_CARRIAGEWAY_W = 7_000
REAL_TOTAL_W = 11_000
REAL_LENGTH = 20_000
REAL_TABLE_LEN = 6_000

LENGTH_S = REAL_LENGTH * FACTOR      # 200_000
WIDTH_S  = REAL_TOTAL_W * FACTOR      # 110_000
TABLE_LEN_S = REAL_TABLE_LEN * FACTOR # 60_000
FOOTPATH_W_S = REAL_FOOTPATH_W * FACTOR  # 20_000
CARRIAGEWAY_W_S = REAL_CARRIAGEWAY_W * FACTOR  # 70_000
LANE_W_S = 3_500 * FACTOR   # 35_000

MARGIN = 5_000
geo_x0 = DETAIL_X0 + MARGIN
geo_y0 = DETAIL_Y0 + MARGIN

# Footpaths – two continuous rectangles
rect(LAYER_FP, geo_x0, geo_y0, LENGTH_S, FOOTPATH_W_S)  # bottom footpath
rect(LAYER_FP, geo_x0, geo_y0 + FOOTPATH_W_S + CARRIAGEWAY_W_S, LENGTH_S, FOOTPATH_W_S)  # top footpath

# Carriageway rectangle (between footpaths)
rect(LAYER_ROAD, geo_x0, geo_y0 + FOOTPATH_W_S, LENGTH_S, CARRIAGEWAY_W_S)

# Lane centreline (dashed)
vline(LAYER_LANE, geo_x0 + LENGTH_S/2, geo_y0 + FOOTPATH_W_S, geo_y0 + FOOTPATH_W_S + CARRIAGEWAY_W_S, "DASHED")

# Raised table – centred longitudinally
TABLE_X0 = geo_x0 + (LENGTH_S - TABLE_LEN_S)/2
TABLE_Y0 = geo_y0 + FOOTPATH_W_S
rect(LAYER_TRAFFIC_CALMING, TABLE_X0, TABLE_Y0, TABLE_LEN_S, CARRIAGEWAY_W_S)

# Zebra stripes – six dashed lines
stripe_spacing = CARRIAGEWAY_W_S / 7
for i in range(1, 7):
    y_str = TABLE_Y0 + i * stripe_spacing
    hline(LAYER_TRAFFIC_CALMING, TABLE_X0, TABLE_X0 + TABLE_LEN_S, y_str, "DASHED")

# Approach ramps – simple inclined lines on both sides of the table
ramp_len = 2_000 * FACTOR  # 20_000
msp.add_line((TABLE_X0 - ramp_len, geo_y0 + FOOTPATH_W_S), (TABLE_X0, TABLE_Y0), dxfattribs={"layer": LAYER_TRAFFIC_CALMING})
msp.add_line((TABLE_X0 + TABLE_LEN_S + ramp_len, geo_y0 + FOOTPATH_W_S), (TABLE_X0 + TABLE_LEN_S, TABLE_Y0), dxfattribs={"layer": LAYER_TRAFFIC_CALMING})

# Directional arrows – one per lane, spaced every 4 m
arrow_spacing = 4_000 * FACTOR
arrow_len = 1_500 * FACTOR
arrow_head_len = 500 * FACTOR
arrow_head_w = 300 * FACTOR

for ix in range(int(geo_x0 + 2_000 * FACTOR), int(geo_x0 + LENGTH_S - 2_000 * FACTOR), arrow_spacing):
    # Lane 1 – Southbound (←)
    y1 = geo_y0 + FOOTPATH_W_S + LANE_W_S/2
    s_start = (ix + arrow_len/2, y1)
    s_end   = (ix - arrow_len/2, y1)
    msp.add_line(s_start, s_end, dxfattribs={"layer": LAYER_LANE})
    msp.add_line(s_end, (s_end[0] + arrow_head_len, y1 + arrow_head_w), dxfattribs={"layer": LAYER_LANE})
    msp.add_line(s_end, (s_end[0] + arrow_head_len, y1 - arrow_head_w), dxfattribs={"layer": LAYER_LANE})
    # Lane 2 – Northbound (→)
    y2 = geo_y0 + FOOTPATH_W_S + LANE_W_S + LANE_W_S/2
    n_start = (ix - arrow_len/2, y2)
    n_end   = (ix + arrow_len/2, y2)
    msp.add_line(n_start, n_end, dxfattribs={"layer": LAYER_LANE})
    msp.add_line(n_end, (n_end[0] - arrow_head_len, y2 + arrow_head_w), dxfattribs={"layer": LAYER_LANE})
    msp.add_line(n_end, (n_end[0] - arrow_head_len, y2 - arrow_head_w), dxfattribs={"layer": LAYER_LANE})

# ---------------------------------------------------------------
# Dimensions for the detail (real design values)
# ---------------------------------------------------------------
len_dim = msp.add_linear_dim(
    base=(geo_x0 - 10_000, geo_y0 + WIDTH_S/2),
    p1=(geo_x0, geo_y0),
    p2=(geo_x0 + LENGTH_S, geo_y0),
    angle=0,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)
len_dim.set_text("20 000 mm (20 m)")
len_dim.render()

wide_dim = msp.add_linear_dim(
    base=(geo_x0 - 10_000, geo_y0 + WIDTH_S/2),
    p1=(geo_x0, geo_y0),
    p2=(geo_x0, geo_y0 + WIDTH_S),
    angle=90,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)
wide_dim.set_text("11 000 mm (11 m)")
wide_dim.render()

car_dim = msp.add_linear_dim(
    base=(geo_x0 - 20_000, geo_y0 + FOOTPATH_W_S + CARRIAGEWAY_W_S/2),
    p1=(geo_x0, geo_y0 + FOOTPATH_W_S),
    p2=(geo_x0, geo_y0 + FOOTPATH_W_S + CARRIAGEWAY_W_S),
    angle=90,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)
car_dim.set_text("7 000 mm (7 m)")
car_dim.render()

fp_dim = msp.add_linear_dim(
    base=(geo_x0 - 30_000, geo_y0 + FOOTPATH_W_S/2),
    p1=(geo_x0, geo_y0),
    p2=(geo_x0, geo_y0 + FOOTPATH_W_S),
    angle=90,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)
fp_dim.set_text("2 000 mm (2 m)")
fp_dim.render()

lane_dim = msp.add_linear_dim(
    base=(geo_x0 - 40_000, geo_y0 + FOOTPATH_W_S + LANE_W_S/2),
    p1=(geo_x0, geo_y0 + FOOTPATH_W_S),
    p2=(geo_x0, geo_y0 + FOOTPATH_W_S + LANE_W_S),
    angle=90,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)
lane_dim.set_text("3 500 mm (3.5 m)")
lane_dim.render()

# Raised table length (conceptual)
tbl_dim = msp.add_linear_dim(
    base=(TABLE_X0 + TABLE_LEN_S/2, TABLE_Y0 - 5_000),
    p1=(TABLE_X0, TABLE_Y0),
    p2=(TABLE_X0 + TABLE_LEN_S, TABLE_Y0),
    angle=0,
    dimstyle=DS,
    dxfattribs={"layer": LAYER_DIM},
)
# Note we display the real length, not the enlarged coordinate value
tbl_dim.set_text("6 000 mm (6 m) – conceptual")

tbl_dim.render()

# ---------------------------------------------------------------
# Callouts – shortened leaders, positioned outside geometry
# ---------------------------------------------------------------
# 1. APPROACH RAMP – upper‑left area (short leader)
add_text(LAYER_TEXT, "APPROACH RAMP", (geo_x0 - 12_000, geo_y0 + WIDTH_S - 8_000), height=TH_SUB, halign="RIGHT")
msp.add_line((geo_x0 - 12_000, geo_y0 + WIDTH_S - 8_000), (TABLE_X0 - ramp_len + 3_000, geo_y0 + FOOTPATH_W_S + 2_000), dxfattribs={"layer": LAYER_TEXT})

# 2. RAISED TABLE – upper‑right area (short leader)
add_text(LAYER_TEXT, "RAISED TABLE", (geo_x0 + LENGTH_S + 12_000, geo_y0 + WIDTH_S - 8_000), height=TH_SUB, halign="LEFT")
msp.add_line((geo_x0 + LENGTH_S + 12_000, geo_y0 + WIDTH_S - 8_000), (TABLE_X0 + TABLE_LEN_S/2, TABLE_Y0 + CARRIAGEWAY_W_S - 2_000), dxfattribs={"layer": LAYER_TEXT})

# 3. ZEBRA CROSSING – lower‑right area (short leader)
add_text(LAYER_TEXT, "ZEBRA CROSSING", (geo_x0 + LENGTH_S + 12_000, geo_y0 + 12_000), height=TH_SUB, halign="LEFT")
msp.add_line((geo_x0 + LENGTH_S + 12_000, geo_y0 + 12_000), (TABLE_X0 + TABLE_LEN_S, TABLE_Y0 + CARRIAGEWAY_W_S/2 - 2_000), dxfattribs={"layer": LAYER_TEXT})

# 4. FOOTPATH – lower‑left area (short leader)
add_text(LAYER_TEXT, "FOOTPATH", (geo_x0 - 12_000, geo_y0 + 12_000), height=TH_SUB, halign="RIGHT")
msp.add_line((geo_x0 - 12_000, geo_y0 + 12_000), (geo_x0, geo_y0 + FOOTPATH_W_S/2), dxfattribs={"layer": LAYER_TEXT})

# Conceptual design note – placed below the panel (outside all graphics)
add_text(LAYER_TEXT,
         "NOTE: Dimensions are conceptual and require site survey and verification against applicable IRC standards and local authority requirements.",
         (DETAIL_X0 + DETAIL_W/2, DETAIL_Y0 - 10_000),
         height=TH_TINY, halign="CENTER")

# ---------------------------------------------------------------------------
# 17. Simple collision detection (unchanged)
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
                    new_xj = xj - 5_000
                    tj.set_placement((new_xj, yj), align=TextEntityAlignment.LEFT)
                    moved = True
        if not moved:
            break
    else:
        print("[WARNING] Collision detection reached max iterations; some overlaps may remain.")

check_collisions()

# ---------------------------------------------------------------------------
# 18. Save DXF (new version – do not alter previous files)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "drawings")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "02_proposed_traffic_calming_road_v9.dxf")

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
