"""Multipole fitting helpers for API diagnostics."""

from __future__ import annotations

import numpy as np


def fit_multipole_ratios(
    field: np.ndarray,
    x_um: np.ndarray,
    y_um: np.ndarray,
    ion: tuple[float, float] = (0.0, 0.0),
    radius_um: float = 80.0,
    order_max: int = 8,
) -> dict[str, float]:
    X, Y = np.meshgrid(x_um, y_um)
    z = (X - ion[0]) + 1j * (Y - ion[1])
    r = np.abs(z)
    mask = r <= radius_um
    if int(mask.sum()) < 2 * order_max + 1:
        return {f"p{n}/p2": 0.0 for n in range(3, order_max + 1)}

    cols = []
    zz = z[mask].ravel()
    for n in range(order_max + 1):
        basis = (zz / max(radius_um, 1.0)) ** n
        cols.append(np.real(basis))
        cols.append(np.imag(basis))
    A = np.vstack(cols).T
    coeffs, *_ = np.linalg.lstsq(A, field[mask].ravel(), rcond=None)
    powers: dict[int, float] = {}
    for n in range(order_max + 1):
        powers[n] = float(np.hypot(coeffs[2 * n], coeffs[2 * n + 1]))
    p2 = max(powers.get(2, 0.0), 1.0e-15)
    return {f"p{n}/p2": powers.get(n, 0.0) / p2 for n in range(3, order_max + 1)}
