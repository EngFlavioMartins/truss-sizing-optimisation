"""ParaView (pvpython) render of the 37-member truss before and after sizing, OpenONDA style.

Usage: pvpython render_truss.py <output png> <design: before|after> [width height]
Reads outputs/render/truss_37.json from compute_truss_37.py.

"before": uniform member areas at the same mass as the sized truss; "after":
the minimum-mass sizing. Both use the same camera and scales. Tubes have radius proportional to sqrt(area), one scale
for both, and are coloured by axial stress / admissible stress with
signed_dark (teal compression, red tension, brightest where over-stressed) on a common
range. Joints and supports are brushed metal on black.
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import onda_style as style  # noqa: E402
from paraview.simple import AppendDatasets, Cone, Show, Sphere, TrivialProducer, Tube  # noqa: E402
from vtkmodules.vtkCommonCore import vtkDoubleArray, vtkPoints  # noqa: E402
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData  # noqa: E402

ROOT = HERE.parents[1]
data = json.loads((ROOT / "outputs" / "render" / "truss_37.json").read_text())
out, which = Path(sys.argv[1]), sys.argv[2]
width, height = (int(a) for a in (sys.argv[3:5] if len(sys.argv) > 4 else (3000, 1400)))
R_MAX = 0.085                                  # tube radius of the largest member [m]; span is 10 m
RANGE = data["ratio_range"]

view = style.setup_view(width, height)
lut = style.lut("stress_ratio", "signed_dark", -RANGE, RANGE)
scale = R_MAX / math.sqrt(max(max(d["areas"]) for d in data["designs"].values()))
joints, supports = [], []      # merged into one display each

for name, design in [(which, data["designs"][which])]:
    dy = 0.0
    pts, lines = vtkPoints(), vtkCellArray()
    radius, ratio = vtkDoubleArray(), vtkDoubleArray()
    radius.SetName("radius")
    ratio.SetName("stress_ratio")
    node_r = {}
    for (a, b), area, sr in zip(data["members"], design["areas"], design["stress_ratio"]):
        r = scale * math.sqrt(area)
        ids = []
        for n in (a, b):
            x, y = data["nodes"][n]
            ids.append(pts.InsertNextPoint(x, y + dy, 0.0))
            radius.InsertNextValue(r)
            ratio.InsertNextValue(sr)
            node_r[n] = max(node_r.get(n, 0.0), r)
        lines.InsertNextCell(2, ids)
    poly = vtkPolyData()
    poly.SetPoints(pts)
    poly.SetLines(lines)
    poly.GetPointData().AddArray(radius)
    poly.GetPointData().AddArray(ratio)
    poly.GetPointData().SetActiveScalars("radius")
    src = TrivialProducer()
    src.GetClientSideObject().SetOutput(poly)
    tube = Tube(Input=src)
    tube.Scalars = ["POINTS", "radius"]
    tube.VaryRadius = "By Absolute Scalar"
    tube.Radius = 1.0
    tube.NumberofSides = 48
    tube.Capping = 1
    style.mapped(Show(tube, view), "stress_ratio", lut, roughness=0.35)
    for n, r in node_r.items():
        x, y = data["nodes"][n]
        joints.append(Sphere(Center=[x, y + dy, 0], Radius=1.12 * r, ThetaResolution=48, PhiResolution=24))
    for n in data["supports"]:
        x, y = data["nodes"][n]
        supports.append(Cone(Center=[x, y + dy - 0.30, 0], Direction=[0, 1, 0], Height=0.38, Radius=0.2, Resolution=64))
style.metal(AppendDatasets(Input=joints), view, mapping="sphere", repeat=(2.0, 1.0))
style.metal(AppendDatasets(Input=supports), view, mapping="cylinder", rgb=(0.62, 0.64, 0.67))
lut.RescaleTransferFunction(-RANGE, RANGE)

view.CameraPosition = [0.6, 3.6, 12.5]
view.CameraFocalPoint = [5.0, 0.45, 0.0]
view.CameraViewUp = [0, 1, 0]
view.CameraViewAngle = 30
style.save(view, out, width, height)
print(out)
