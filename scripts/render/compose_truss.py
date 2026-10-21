"""Add the LaTeX overlay (labels and the stress colour bar) to the truss render.

Usage: python compose_truss.py <raw png> <output stem>
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from overlay import compose  # noqa: E402

raw, stem = Path(sys.argv[1]), Path(sys.argv[2])
rng = json.loads((HERE.parents[1] / "outputs" / "render" / "truss_37.json").read_text())["ratio_range"]
frac = lambda v: 0.5 + 0.5 * v / rng
compose(raw, stem,
        bar=dict(name="signed_dark", vmin=-rng, vmax=rng, x=76, y=8, height=26,
                 title=r"$\sigma/\sigma_{\mathrm{adm}}$",
                 ticks=[(frac(-2), "$-$2"), (frac(-1), "$-$1"), (frac(0), "0"), (frac(1), "1"), (frac(2), "2")]),
        labels=[(4, 52.5, "Uniform areas", "north west"), (4, 31.0, "Sized", "north west")])
