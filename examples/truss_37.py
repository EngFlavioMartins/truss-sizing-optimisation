"""37-member isostatic truss of Fig. 6 in Martins, Avila & da Silva (2019)."""
import numpy as np

from truss_sizing import Truss


def truss_37(span_panels=10, L=1.0, F=1000.0):
    bottom = [(i * L, 0.0) for i in range(span_panels + 1)]               # nodes 0..10
    top = [(i * L, L) for i in range(1, span_panels)]                      # nodes 11..19
    nodes = np.array(bottom + top)
    nb = span_panels + 1
    T = lambda i: nb + i - 1                                               # top node above bottom node i
    members = []
    members += [(T(i), T(i + 1)) for i in range(1, span_panels - 1)]       # top chord (8)
    members += [(i, i + 1) for i in range(span_panels)]                    # bottom chord (10)
    members += [(i, T(i)) for i in range(1, span_panels)]                  # verticals (9)
    half = span_panels // 2
    members += [(0, T(1)), (span_panels, T(span_panels - 1))]              # end diagonals
    members += [(T(i), i + 1) for i in range(1, half)]                     # diagonals down to mid-span
    members += [(i - 1, T(i)) for i in range(half + 1, span_panels)]
    members = np.array(members)
    loads = {T(i): (0.0, -F) for i in range(1, span_panels)}
    supports = {0: (True, True), span_panels: (False, True)}
    return Truss(nodes, members, supports, loads)


if __name__ == "__main__":
    from truss_sizing import size_truss
    t = truss_37()
    print(len(t.nodes), "nodes,", len(t.members), "members, isostatic:", t.is_isostatic())
    x, N, s, m = size_truss(t)
    print(f"minimum mass {m:.2f} kg; max |sigma|/sigma_adm = {np.abs(s).max() / 50e6:.3f}")
