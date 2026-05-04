"""Finite-difference Laplace solver used by the compute backend."""

from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

from .geometry import electrode_mask
from .models import Electrode


def make_grid(domain_um: float, grid_size: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    x = np.linspace(-domain_um, domain_um, grid_size)
    y = np.linspace(-domain_um, domain_um, grid_size)
    X, Y = np.meshgrid(x, y)
    return x, y, X, Y


def solve_laplace_fd(
    electrodes: list[Electrode],
    domain_um: float,
    grid_size: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[np.ndarray]]:
    """Solve Laplace's equation with fixed electrode and outer-boundary pixels."""
    x, y, X, Y = make_grid(domain_um, grid_size)
    ny, nx = X.shape
    potential = np.zeros((ny, nx), dtype=float)
    fixed = np.zeros((ny, nx), dtype=bool)
    masks: list[np.ndarray] = []

    for electrode in electrodes:
        mask = electrode_mask(electrode, X, Y)
        masks.append(mask)
        fixed[mask] = True
        potential[mask] = electrode.voltage

    fixed[0, :] = True
    fixed[-1, :] = True
    fixed[:, 0] = True
    fixed[:, -1] = True

    unknown = ~fixed
    index = -np.ones((ny, nx), dtype=int)
    index[unknown] = np.arange(int(unknown.sum()))

    rows: list[int] = []
    cols: list[int] = []
    data: list[float] = []
    rhs = np.zeros(int(unknown.sum()), dtype=float)

    for iy in range(1, ny - 1):
        for ix in range(1, nx - 1):
            row = index[iy, ix]
            if row < 0:
                continue
            rows.append(row)
            cols.append(row)
            data.append(4.0)
            for jy, jx in ((iy - 1, ix), (iy + 1, ix), (iy, ix - 1), (iy, ix + 1)):
                col = index[jy, jx]
                if col >= 0:
                    rows.append(row)
                    cols.append(col)
                    data.append(-1.0)
                else:
                    rhs[row] += potential[jy, jx]

    if rhs.size:
        matrix = sparse.csr_matrix((data, (rows, cols)), shape=(rhs.size, rhs.size))
        potential[unknown] = spsolve(matrix, rhs)

    for electrode, mask in zip(electrodes, masks):
        potential[mask] = electrode.voltage

    return potential, x, y, X, Y, fixed, masks


def find_rf_null(potential: np.ndarray, x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Find the lowest electric-field location, falling back to the origin."""
    gy, gx = np.gradient(potential, y, x, edge_order=2)
    field2 = gx**2 + gy**2
    iy, ix = np.unravel_index(int(np.argmin(field2)), field2.shape)
    return float(x[ix]), float(y[iy])
