"""ParaView (pvpython) animation frames: the 37-member truss morphing into its sized design.

Usage: pvpython render_animation.py <morph json> <frame directory>
The json (from make_animation.py) holds the nodes, members, supports and, per frame, the
member areas and stress / admissible stress. Same look as the still figure: tube radius
proportional to sqrt(area), colour signed_dark (teal compression, red tension), brushed-metal
joints and supports on black.
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import onda_style as style  # noqa: E402
from paraview.simple import AppendDatasets, Cone, Glyph, Show, TrivialProducer, Tube  # noqa: E402
from vtkmodules.vtkCommonCore import vtkDoubleArray, vtkPoints  # noqa: E402
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData  # noqa: E402

data = json.loads(Path(sys.argv[1]).read_text())
out = Path(sys.argv[2])
width, height = 1500, 700
R_MAX = 0.085
RANGE = data["ratio_range"]
scale = R_MAX / math.sqrt(max(max(f["areas"]) for f in data["frames"]))


def geometry(frame):
    """Members as lines (radius, stress_ratio on points) and joints as points (radius)."""
    pts, lines = vtkPoints(), vtkCellArray()
    radius, ratio = vtkDoubleArray(), vtkDoubleArray()
    radius.SetName("radius")
    ratio.SetName("stress_ratio")
    node_r = {}
    for (a, b), area, sr in zip(data["members"], frame["areas"], frame["stress_ratio"]):
        r = scale * math.sqrt(area)
        ids = []
        for n in (a, b):
            x, y = data["nodes"][n]
            ids.append(pts.InsertNextPoint(x, y, 0.0))
            radius.InsertNextValue(r)
            ratio.InsertNextValue(sr)
            node_r[n] = max(node_r.get(n, 0.0), r)
        lines.InsertNextCell(2, ids)
    members = vtkPolyData()
    members.SetPoints(pts)
    members.SetLines(lines)
    members.GetPointData().AddArray(radius)
    members.GetPointData().AddArray(ratio)
    members.GetPointData().SetActiveScalars("radius")

    jp, jr = vtkPoints(), vtkDoubleArray()
    jr.SetName("diameter")
    for n, r in sorted(node_r.items()):
        x, y = data["nodes"][n]
        jp.InsertNextPoint(x, y, 0.0)
        jr.InsertNextValue(2 * 1.12 * r)
    joints = vtkPolyData()
    joints.SetPoints(jp)
    joints.GetPointData().AddArray(jr)
    return members, joints


view = style.setup_view(width, height)
lut = style.lut("stress_ratio", "signed_dark", -RANGE, RANGE)
members, joints = geometry(data["frames"][0])
m_src, j_src = TrivialProducer(), TrivialProducer()
m_src.GetClientSideObject().SetOutput(members)
j_src.GetClientSideObject().SetOutput(joints)
tube = Tube(Input=m_src)
tube.Scalars = ["POINTS", "radius"]
tube.VaryRadius = "By Absolute Scalar"
tube.Radius = 1.0
tube.NumberofSides = 48
tube.Capping = 1
style.mapped(Show(tube, view), "stress_ratio", lut, roughness=0.35)
balls = Glyph(Input=j_src, GlyphType="Sphere")
balls.GlyphType.Radius = 0.5
balls.GlyphType.ThetaResolution = 48
balls.GlyphType.PhiResolution = 24
balls.ScaleArray = ["POINTS", "diameter"]
balls.ScaleFactor = 1.0
balls.GlyphMode = "All Points"
style.metal(balls, view, mapping="sphere", repeat=(2.0, 1.0))
supports = []
for n in data["supports"]:
    x, y = data["nodes"][n]
    supports.append(Cone(Center=[x, y - 0.30, 0], Direction=[0, 1, 0], Height=0.38, Radius=0.2, Resolution=64))
style.metal(AppendDatasets(Input=supports), view, mapping="cylinder", rgb=(0.62, 0.64, 0.67))
lut.RescaleTransferFunction(-RANGE, RANGE)

view.CameraPosition = [0.6, 3.6, 12.5]
view.CameraFocalPoint = [5.0, 0.45, 0.0]
view.CameraViewUp = [0, 1, 0]
view.CameraViewAngle = 30
out.mkdir(parents=True, exist_ok=True)
for k, frame in enumerate(data["frames"]):
    members, joints = geometry(frame)
    m_src.GetClientSideObject().SetOutput(members)
    j_src.GetClientSideObject().SetOutput(joints)
    m_src.MarkModified(m_src)
    j_src.MarkModified(j_src)
    style.save(view, out / f"frame_{k:03d}.png", width, height)
    print(k, end=" ", flush=True)
print()
