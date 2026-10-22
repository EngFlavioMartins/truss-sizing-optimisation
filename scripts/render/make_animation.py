"""Animation for the README: the 37-member truss morphing from uniform areas into its sizing.

Sizes the truss with this package (as compute_truss_37.py), then blends the member areas
geometrically from the uniform design (same mass) to the minimum-mass design and back,
recomputing the member stresses at every step. The colour shows the over-stressed members
of the uniform truss cooling to the admissible stress as material moves into them.
Frames are rendered with ParaView (render_animation.py); writes docs/assets/animation.webp.
Run:  python scripts/render/make_animation.py   (needs ParaView; set PVPYTHON if it is not found)
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "examples"), str(HERE)]
from gif import crop_union, pvpython, save_gif  # noqa: E402
from truss_37 import truss_37  # noqa: E402
from truss_sizing import size_truss  # noqa: E402
from truss_sizing.truss import influence_matrix  # noqa: E402

SIGMA_ADM, RATIO_RANGE = 50e6, 2.25
MORPH, HOLD = 48, 14                       # frames for each morph and for each rest

t = truss_37()
x, _, _, mass = size_truss(t, sigma_adm=SIGMA_ADM)
C, CF = influence_matrix(t)
x_uniform = np.full_like(x, mass / (t.rho * t.lengths.sum()))
s = np.linspace(0, 1, MORPH)
s = s * s * (3 - 2 * s)                    # ease in and out
path = list(np.r_[np.zeros(HOLD), s, np.ones(HOLD), s[::-1]])
frames = []
for f in path:
    a = x_uniform ** (1 - f) * x ** f
    frames.append({"areas": a.tolist(), "stress_ratio": ((C @ a + CF) / a / SIGMA_ADM).tolist()})

with tempfile.TemporaryDirectory() as tmp:
    morph = Path(tmp) / "morph.json"
    morph.write_text(json.dumps({"nodes": t.nodes.tolist(), "members": t.members.tolist(),
                                 "supports": [int(n) for n in t.supports], "ratio_range": RATIO_RANGE,
                                 "frames": frames}))
    subprocess.run([pvpython(), str(HERE / "render_animation.py"), str(morph), tmp], check=True)
    images = crop_union([Image.open(p) for p in sorted(Path(tmp).glob("frame_*.png"))])
save_gif(images, ROOT / "docs" / "assets" / "animation.webp", fps=20, width=840)
