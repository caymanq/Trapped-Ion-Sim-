"""Physics validation checks shared by the API and tests."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_dilation

from .geometry import electrode_mask
from .models import Electrode, ValidationResult


def _normalised_laplace(V: np.ndarray, x_um: np.ndarray, y_um: np.ndarray) -> np.ndarray:
    dx = float(np.mean(np.diff(x_um)))
    dy = float(np.mean(np.diff(y_um)))
    lap = np.zeros_like(V, dtype=float)
    lap[1:-1, 1:-1] = (
        (V[1:-1, 2:] - 2.0 * V[1:-1, 1:-1] + V[1:-1, :-2]) / dx**2
        + (V[2:, 1:-1] - 2.0 * V[1:-1, 1:-1] + V[:-2, 1:-1]) / dy**2
    )
    scale = max(float(np.nanmax(np.abs(V))), 1.0)
    return np.abs(lap) * max(dx, dy) ** 2 / scale


def validate_solution(
    potential: np.ndarray,
    x_um: np.ndarray,
    y_um: np.ndarray,
    X: np.ndarray,
    Y: np.ndarray,
    electrodes: list[Electrode],
    fixed: np.ndarray,
    tol: float = 1.0e-3,
    bulk_layers: int = 3,
) -> ValidationResult:
    lap = _normalised_laplace(potential, x_um, y_um)
    vacuum = ~fixed
    interior = np.zeros_like(vacuum, dtype=bool)
    interior[1:-1, 1:-1] = True
    vacuum &= interior

    near_fixed = binary_dilation(fixed, iterations=bulk_layers)
    bulk = vacuum & ~near_fixed
    lap_max = float(np.nanmax(lap[vacuum])) if vacuum.any() else 0.0
    lap_bulk_max = float(np.nanmax(lap[bulk])) if bulk.any() else lap_max

    warnings: list[str] = []
    max_rel = 0.0
    for electrode in electrodes:
        mask = electrode_mask(electrode, X, Y)
        if not mask.any():
            warnings.append(f"Electrode {electrode.id} is not represented on the grid.")
            max_rel = max(max_rel, 1.0)
            continue
        err = float(np.nanmax(np.abs(potential[mask] - electrode.voltage)))
        denom = max(abs(electrode.voltage), 1.0)
        max_rel = max(max_rel, err / denom)

    return ValidationResult(
        laplace_passed=lap_max <= tol,
        laplace_bulk_passed=lap_bulk_max <= tol,
        electrode_voltage_passed=max_rel <= tol,
        normalised_laplace_max=lap_max,
        normalised_laplace_bulk_max=lap_bulk_max,
        electrode_voltage_max_relative_error=float(max_rel),
        all_passed=(lap_bulk_max <= tol and max_rel <= tol),
        warnings=warnings,
    )
