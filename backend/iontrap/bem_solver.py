"""Boundary-element solver extracted from ``multipole_BEM.ipynb``."""

from __future__ import annotations

import numpy as np

from .geometry import electrode_mask
from .models import Electrode


def discretize_electrodes(electrodes: list[Electrode], n_per_side: int = 18) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    positions: list[tuple[float, float]] = []
    lengths: list[float] = []
    potentials: list[float] = []
    for electrode in electrodes:
        x0, x1 = electrode.cx - electrode.width / 2.0, electrode.cx + electrode.width / 2.0
        y0, y1 = electrode.cy - electrode.height / 2.0, electrode.cy + electrode.height / 2.0
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for index, (ax, ay) in enumerate(corners):
            bx, by = corners[(index + 1) % 4]
            side_len = float(np.hypot(bx - ax, by - ay))
            n = max(2, int(round(n_per_side * side_len / max(electrode.width, electrode.height))))
            for j in range(n):
                t = (j + 0.5) / n
                positions.append((ax + t * (bx - ax), ay + t * (by - ay)))
                lengths.append(side_len / n)
                potentials.append(electrode.voltage)
    return np.asarray(positions), np.asarray(lengths), np.asarray(potentials)


def build_influence_matrix(positions: np.ndarray, lengths: np.ndarray) -> np.ndarray:
    dx = positions[:, np.newaxis, 0] - positions[np.newaxis, :, 0]
    dy = positions[:, np.newaxis, 1] - positions[np.newaxis, :, 1]
    dist = np.sqrt(dx**2 + dy**2)
    dist = np.maximum(dist, (lengths[:, np.newaxis] + lengths[np.newaxis, :]) * 1e-14 + 1e-18)
    np.fill_diagonal(dist, 1.0)
    matrix = -(lengths[np.newaxis, :] / (2.0 * np.pi)) * np.log(dist)
    diag = (lengths / (2.0 * np.pi)) * (1.0 - np.log(lengths / 2.0))
    np.fill_diagonal(matrix, diag)
    return matrix


def evaluate_bem_potential(positions: np.ndarray, charges: np.ndarray, eval_pts: np.ndarray) -> np.ndarray:
    phi = np.zeros(eval_pts.shape[0], dtype=float)
    chunk = 50000
    for start in range(0, eval_pts.shape[0], chunk):
        end = min(start + chunk, eval_pts.shape[0])
        dx = eval_pts[start:end, 0, np.newaxis] - positions[np.newaxis, :, 0]
        dy = eval_pts[start:end, 1, np.newaxis] - positions[np.newaxis, :, 1]
        dist = np.maximum(np.sqrt(dx**2 + dy**2), 1e-30)
        phi[start:end] = np.dot(-np.log(dist) / (2.0 * np.pi), charges)
    return phi


def solve_laplace_bem(
    electrodes: list[Electrode],
    domain_um: float,
    grid_size: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[np.ndarray]]:
    x = np.linspace(-domain_um, domain_um, grid_size)
    y = np.linspace(-domain_um, domain_um, grid_size)
    X, Y = np.meshgrid(x, y)
    fixed = np.zeros_like(X, dtype=bool)
    v_map = np.zeros_like(X, dtype=float)
    masks: list[np.ndarray] = []
    for electrode in electrodes:
        mask = electrode_mask(electrode, X, Y)
        masks.append(mask)
        fixed[mask] = True
        v_map[mask] = electrode.voltage

    positions, lengths, potentials = discretize_electrodes(electrodes)
    matrix = build_influence_matrix(positions, lengths)
    charges = np.linalg.solve(matrix, potentials)
    eval_pts = np.column_stack([X.ravel(), Y.ravel()])
    potential = evaluate_bem_potential(positions, charges, eval_pts).reshape(X.shape)
    potential[fixed] = v_map[fixed]
    return potential, x, y, X, Y, fixed, masks
