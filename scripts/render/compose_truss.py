"""Stack the uniform and sized truss renders and add the LaTeX overlay.

Usage: python compose_truss.py <uniform png> <sized png> <output stem>
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from overlay import compose  # noqa: E402

before, after, stem = (Path(a) for a in sys.argv[1:4])
rng = json.loads((HERE.parents[1] / "outputs" / "render" / "truss_37.json").read_text())["ratio_range"]
frac = lambda v: 0.5 + 0.5 * v / rng
compose([(before, "Uniform areas"), (after, "Sized")], stem,
        bar=dict(name="signed_dark", vmin=-rng, vmax=rng, title=r"$\sigma/\sigma_{\mathrm{adm}}$",
                 ticks=[(frac(-2), "$-$2"), (frac(0), "0"), (frac(2), "2")]))
