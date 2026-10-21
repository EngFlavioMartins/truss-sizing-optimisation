"""Size the 37-member truss and write both designs for the ParaView render.

"before": every member has the same area, chosen so the truss has the same
mass as the sized one; "after": the minimum-mass sizing.
"""
import json
import sys
from pathlib import Path

import cmcrameri.cm as cmc
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "examples")]
from truss_37 import truss_37  # noqa: E402
from truss_sizing import size_truss  # noqa: E402
from truss_sizing.truss import influence_matrix  # noqa: E402

SIGMA_ADM = 50e6
RATIO_RANGE = 2.25        # colour range of sigma / sigma_adm, common to both designs

t = truss_37()
x, N, s, mass = size_truss(t, sigma_adm=SIGMA_ADM)
C, CF = influence_matrix(t)
x_uniform = np.full_like(x, mass / (t.rho * t.lengths.sum()))
s_uniform = (C @ x_uniform + CF) / x_uniform
designs = {"before": (x_uniform, s_uniform), "after": (x, s)}
out = ROOT / "outputs" / "render" / "truss_37.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "nodes": t.nodes.tolist(), "members": t.members.tolist(),
    "designs": {k: {"areas": a.tolist(), "stress_ratio": (r / SIGMA_ADM).tolist()} for k, (a, r) in designs.items()},
    "supports": [int(n) for n in t.supports], "mass_kg": mass, "ratio_range": RATIO_RANGE,
    # Crameri "vik" sampled for ParaView: (value, r, g, b) over the stress-ratio range
    "vik_rgb_points": [v for q in np.linspace(0, 1, 65) for v in ((2 * q - 1) * RATIO_RANGE, *cmc.vik(q)[:3])],
}, indent=1))
for k, (a, r) in designs.items():
    print(f"{k}: mass {t.rho * (t.lengths * a).sum():.2f} kg, max |sigma|/sigma_adm = {np.abs(r).max() / SIGMA_ADM:.2f}")
