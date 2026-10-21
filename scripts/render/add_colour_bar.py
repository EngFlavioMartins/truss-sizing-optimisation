"""Add one horizontal colour bar (sigma / sigma_adm, Crameri "vik") under the truss render.

Labels are typeset with LaTeX at 4.5 % of the image width, so they stay legible
when the image is shown 600 px wide. The admissible limits +/-1 are marked.
Usage: python add_colour_bar.py <render png> <output stem>
"""
import io
import json
import sys
from pathlib import Path

import cmcrameri.cm as cmc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
src, stem = Path(sys.argv[1]), Path(sys.argv[2])
rng = json.loads((ROOT / "outputs" / "render" / "truss_37.json").read_text())["ratio_range"]
img = Image.open(src).convert("RGB")
W, H = img.size

plt.rcParams.update({"text.usetex": True, "font.family": "serif", "font.size": 11})
dpi = 200
fig_w = 0.5 * W / dpi
fig = plt.figure(figsize=(fig_w, 0.62 * fig_w / 4.2), dpi=dpi)
ax = fig.add_axes([0.06, 0.62, 0.88, 0.2])
norm = matplotlib.colors.Normalize(-rng, rng)
cb = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap=cmc.vik), cax=ax, orientation="horizontal")
cb.set_ticks([-2, -1, 0, 1, 2])
cb.ax.tick_params(labelsize=0.045 * W * 72 / dpi, length=0, pad=4)
cb.outline.set_visible(False)
for v in (-1, 1):
    ax.axvline(v, color="#15212B", lw=1.6)
cb.set_label(r"$\sigma/\sigma_{\mathrm{adm}}$", fontsize=0.045 * W * 72 / dpi, labelpad=4)
buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=dpi, facecolor="white", bbox_inches="tight", pad_inches=0.05)
plt.close(fig)
bar = Image.open(buf).convert("RGB")
img.paste(bar, ((W - bar.width) // 2, H - bar.height - int(0.02 * H)))
img.save(stem.with_suffix(".png"), optimize=True)
img.save(stem.with_suffix(".webp"), quality=85, method=6)
for ext in (".png", ".webp"):
    print(stem.with_suffix(ext), f"{stem.with_suffix(ext).stat().st_size / 1e3:.0f} kB")
