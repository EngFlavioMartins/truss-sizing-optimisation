# Truss sizing optimisation

**Minimum-mass sizing of isostatic trusses as one linear programme.**

![The 37-member benchmark truss at equal mass, with uniform member areas (top) and after linear sizing (bottom), coloured by axial stress over admissible stress](docs/assets/render.webp)

Minimum-mass sizing of statically determinate (isostatic) planar trusses under external and self-weight loads, using the linear "indirect method" of

> F. A. C. Martins, J. P. J. Avila and M. A. da Silva (2019). A linear approach for sizing optimization of isostatic trussed structures subjected to external and self-weight loads. *International Journal of Steel Structures* 19(4), 1146–1157. [doi:10.1007/s13296-018-0194-8](https://doi.org/10.1007/s13296-018-0194-8)

The original 2018 MATLAB code is not available. This Python version is a re-implementation from the paper.

## Method

In an isostatic truss, member forces do not depend on member areas. The force in member *i* is therefore linear in the design areas *x*: N<sub>i</sub> = Σ<sub>j</sub> C<sub>ij</sub> x<sub>j</sub> + C<sub>F,i</sub>. Here C<sub>ij</sub> is the force caused by the self-weight of member *j* at unit area, and C<sub>F,i</sub> is the force caused by the external loads. Building these coefficients takes *n* + 1 linear finite-element solves. The stress limit |N<sub>i</sub>/x<sub>i</sub>| ≤ σ<sub>adm</sub> then gives two linear inequalities per member, so minimum mass is a linear programme (Eqs. 4–7 of the paper). It is solved here with SciPy's HiGHS interior-point method.

## Quick start

```bash
pip install numpy scipy
PYTHONPATH=src python examples/truss_37.py
```

The 37-member truss of Fig. 6 (ρ = 2800 kg/m³, E = 80 GPa, σ<sub>adm</sub> = 50 MPa, 5×10⁻⁶ ≤ x ≤ 1 m²) sizes to 13.15 kg. The paper reports 13.35 kg (indirect method) and 13.23 kg (direct method); the linear programme here is solved to optimality.

## Repository guide

| Location | Purpose |
| --- | --- |
| `src/truss_sizing/` | Truss model, linear FE solve and linear sizing problem |
| `examples/truss_37.py` | Geometry and loads of the 37-member benchmark |
| `scripts/render/` | Scripts that make the website image (ParaView 5.12+ `pvpython`, `cmcrameri`, Pillow, Matplotlib with LaTeX) |

To reproduce the website image:

```bash
python scripts/render/compute_truss_37.py
pvpython scripts/render/render_truss_37.py
python scripts/render/add_colour_bar.py outputs/render/truss-sizing-raw.png outputs/render/truss-sizing
```

The image compares two trusses of equal mass. In the uniform design (top), every member has the same area, and the most loaded members reach 2.22 σ<sub>adm</sub>. The sized design (bottom) keeps every member within the admissible stress. A uniform design needs 29.7 kg to meet the stress limit.

## Citing

This code re-implements F. A. C. Martins, J. P. J. Avila and M. A. da Silva (2019), A linear approach for sizing optimization of isostatic trussed structures subjected to external and self-weight loads, *International Journal of Steel Structures* 19(4), 1146–1157, [doi:10.1007/s13296-018-0194-8](https://doi.org/10.1007/s13296-018-0194-8).

GitHub's *Cite this repository* button uses [CITATION.cff](CITATION.cff).

## Licence

MIT; see [LICENSE](LICENSE).
