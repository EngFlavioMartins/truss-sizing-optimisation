"""ParaView (pvpython) render of the 37-member truss before and after sizing.

Top: uniform member areas at the same mass as the sized truss. Bottom: the
minimum-mass sizing. Tubes have radius proportional to sqrt(area) (one scale
for both) and are coloured by axial stress / admissible stress with Crameri's
"vik" on a common range. Run with pvpython after compute_truss_37.py;
finish_image.py then adds the colour bar.
"""
import json
import math
import sys
from pathlib import Path

from paraview.simple import (Cone, ColorBy, GetActiveViewOrCreate, GetColorTransferFunction,
                             SaveScreenshot, Show, Sphere, TrivialProducer, Tube)
from vtkmodules.vtkCommonCore import vtkDoubleArray, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "render"
data = json.loads((OUT / "truss_37.json").read_text())
R_MAX = 0.085            # tube radius of the largest member in either design [m]; span is 10 m
OFFSET = {"before": 2.3, "after": 0.0}    # vertical placement of the two trusses [m]
width, height = (int(a) for a in (sys.argv[1:3] if len(sys.argv) > 2 else (2400, 1600)))

view = GetActiveViewOrCreate("RenderView")
view.ViewSize = [width, height]
view.OrientationAxesVisibility = 0
view.UseColorPaletteForBackground = 0
view.Background = [1, 1, 1]
# OSPRay ray caster on white: Blinn-Phong shading like the OpenONDA tutorial
# renders, plus ambient occlusion where members meet.
view.EnableRayTracing = 1
view.BackEnd = "OSPRay raycaster"
view.SamplesPerPixel = 32
view.AmbientSamples = 8
view.Shadows = 1

lut = GetColorTransferFunction("stress_ratio")
lut.RGBPoints = data["vik_rgb_points"]
lut.ColorSpace = "RGB"
lut.AutomaticRescaleRangeMode = "Never"
scale = R_MAX / math.sqrt(max(max(d["areas"]) for d in data["designs"].values()))

for name, design in data["designs"].items():
    dy = OFFSET[name]
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
    d = Show(tube, view)
    ColorBy(d, ("POINTS", "stress_ratio"))
    d.LookupTable = lut
    d.SetScalarBarVisibility(view, False)
    d.Ambient, d.Diffuse, d.Specular, d.SpecularPower = 0.2, 0.8, 0.35, 40
    # joints: neutral grey spheres just larger than the thickest member at each node
    for n, r in node_r.items():
        x, y = data["nodes"][n]
        s = Show(Sphere(Center=[x, y + dy, 0], Radius=1.12 * r, ThetaResolution=48, PhiResolution=24), view)
        s.AmbientColor = s.DiffuseColor = [0.72, 0.74, 0.76]
        s.Ambient, s.Diffuse, s.Specular, s.SpecularPower = 0.22, 0.78, 0.6, 40
    # supports: grey cones under the two support nodes
    for n in data["supports"]:
        x, y = data["nodes"][n]
        c = Show(Cone(Center=[x, y + dy - 0.30, 0], Direction=[0, 1, 0], Height=0.38, Radius=0.2, Resolution=64), view)
        c.AmbientColor = c.DiffuseColor = [0.48, 0.51, 0.55]
        c.Ambient, c.Diffuse = 0.22, 0.78
lut.RescaleTransferFunction(-data["ratio_range"], data["ratio_range"])

view.CameraPosition = [-0.6, 4.6, 13.6]
view.CameraFocalPoint = [4.9, 1.35, 0.0]
view.CameraViewUp = [0, 1, 0]
view.CameraViewAngle = 30

OUT.mkdir(parents=True, exist_ok=True)
SaveScreenshot(str(OUT / "truss-sizing-raw.png"), view, ImageResolution=[width, height], TransparentBackground=0)
print(OUT / "truss-sizing-raw.png")
