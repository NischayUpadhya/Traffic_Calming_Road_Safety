import os, ezdxf
from ezdxf.addons.drawing import MatplotlibBackend, Frontend

project_root = r"C:\\final year\\Traffic_Calming_Road_Safety"
v10_path = os.path.join(project_root, "drawings", "02_proposed_traffic_calming_road_v10.dxf")
preview_path = os.path.join(project_root, "reports", "cad_v10_preview.png")

if not os.path.isfile(v10_path):
    raise FileNotFoundError(f"V10 DXF not found at {v10_path}")

doc = ezdxf.readfile(v10_path)
backend = MatplotlibBackend()
frontend = Frontend(backend)
frontend.draw_layout(doc.modelspace(), finalize=True)
backend.figure.savefig(preview_path)
print('Preview saved to', preview_path)
