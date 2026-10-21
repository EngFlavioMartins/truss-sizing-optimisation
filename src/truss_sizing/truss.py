"""Planar pin-jointed truss: linear FE solve and the linear sizing problem.

For a statically determinate truss, member forces do not depend on the member
areas. The force in member i is therefore linear in the design areas x:

    N_i(x) = sum_j C_ij x_j + C_F,i

where C_ij is the force in i caused by the self-weight of member j at unit
area, and C_F,i the force caused by the external loads (Eq. 4-5 of the paper).
The stress constraint |N_i / x_i| <= sigma_adm becomes two linear inequalities
per member (Eq. 6-7), so minimum mass is a linear programme.
"""
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import linprog

G = 9.81


@dataclass
class Truss:
    nodes: np.ndarray                 # (n_nodes, 2) coordinates [m]
    members: np.ndarray               # (n_members, 2) node indices
    supports: dict                    # node -> (fix_x, fix_y)
    loads: dict = field(default_factory=dict)  # node -> (Fx, Fy) [N]
    E: float = 80e9                   # Pa
    rho: float = 2800.0               # kg/m^3

    @property
    def lengths(self):
        d = self.nodes[self.members[:, 1]] - self.nodes[self.members[:, 0]]
        return np.hypot(d[:, 0], d[:, 1])

    def is_isostatic(self):
        n_fixed = sum(int(fx) + int(fy) for fx, fy in self.supports.values())
        return len(self.members) + n_fixed == 2 * len(self.nodes)


def member_forces(truss, nodal_loads, areas=None):
    """Axial forces (tension positive) from a linear stiffness solve."""
    n_nodes, n_mem = len(truss.nodes), len(truss.members)
    areas = np.ones(n_mem) if areas is None else np.asarray(areas, float)
    K = np.zeros((2 * n_nodes, 2 * n_nodes))
    L = truss.lengths
    d = truss.nodes[truss.members[:, 1]] - truss.nodes[truss.members[:, 0]]
    c, s = d[:, 0] / L, d[:, 1] / L
    for m, (a, b) in enumerate(truss.members):
        t = np.array([-c[m], -s[m], c[m], s[m]])
        k = truss.E * areas[m] / L[m] * np.outer(t, t)
        dofs = [2 * a, 2 * a + 1, 2 * b, 2 * b + 1]
        K[np.ix_(dofs, dofs)] += k
    fixed = [2 * n + i for n, fix in truss.supports.items() for i in (0, 1) if fix[i]]
    free = np.setdiff1d(np.arange(2 * n_nodes), fixed)
    u = np.zeros(2 * n_nodes)
    u[free] = np.linalg.solve(K[np.ix_(free, free)], nodal_loads[free])
    du = np.stack([u[2 * truss.members[:, 1]] - u[2 * truss.members[:, 0]],
                   u[2 * truss.members[:, 1] + 1] - u[2 * truss.members[:, 0] + 1]], axis=1)
    return truss.E * areas / L * (c * du[:, 0] + s * du[:, 1])


def _external_load_vector(truss):
    f = np.zeros(2 * len(truss.nodes))
    for n, (fx, fy) in truss.loads.items():
        f[2 * n] += fx
        f[2 * n + 1] += fy
    return f


def influence_matrix(truss):
    """C (forces per unit area of each member's self-weight) and C_F (external loads).

    Needs n_members + 1 linear solves, as in the paper's indirect method.
    """
    n_mem = len(truss.members)
    C = np.zeros((n_mem, n_mem))
    weight = truss.rho * G * truss.lengths          # N per m^2 of area
    for j, (a, b) in enumerate(truss.members):
        f = np.zeros(2 * len(truss.nodes))
        f[2 * a + 1] -= 0.5 * weight[j]             # lumped half to each end
        f[2 * b + 1] -= 0.5 * weight[j]
        C[:, j] = member_forces(truss, f)
    CF = member_forces(truss, _external_load_vector(truss))
    return C, CF


def size_truss(truss, sigma_adm=50e6, lower=5e-6, upper=1.0):
    """Minimum-mass areas subject to |sigma_i| <= sigma_adm and lower <= x <= upper.

    Returns (areas, member forces, stresses, mass).
    """
    if not truss.is_isostatic():
        raise ValueError("the linear formulation assumes a statically determinate truss")
    C, CF = influence_matrix(truss)
    n = len(CF)
    A_ub = np.vstack([C - sigma_adm * np.eye(n), -C - sigma_adm * np.eye(n)])
    b_ub = np.concatenate([-CF, CF])
    cost = truss.rho * truss.lengths
    res = linprog(cost, A_ub=A_ub, b_ub=b_ub, bounds=[(lower, upper)] * n, method="highs-ipm")
    if not res.success:
        raise RuntimeError(res.message)
    x = res.x
    forces = C @ x + CF
    return x, forces, forces / x, float(cost @ x)
