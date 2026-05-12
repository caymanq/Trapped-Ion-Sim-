"""Derived pseudopotential metrics for trap design."""

from __future__ import annotations

import math

import numpy as np

from .constants import ATOMIC_MASS, ELEMENTARY_CHARGE
from .models import DerivedMetrics, HarmonicityMetrics, SecularFrequencyMetrics


MICRO_EV_TO_J = ELEMENTARY_CHARGE * 1.0e-6
UM2_TO_M2_INV = 1.0e12


def _local_points(
    field: np.ndarray,
    x_um: np.ndarray,
    y_um: np.ndarray,
    ion: tuple[float, float],
    radius_um: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    X, Y = np.meshgrid(x_um, y_um)
    dx = X - ion[0]
    dy = Y - ion[1]
    r = np.hypot(dx, dy)
    mask = r <= radius_um
    return dx[mask].ravel(), dy[mask].ravel(), field[mask].ravel()


def fit_local_polynomial(
    field: np.ndarray,
    x_um: np.ndarray,
    y_um: np.ndarray,
    ion: tuple[float, float] = (0.0, 0.0),
    radius_um: float = 80.0,
) -> dict[str, float]:
    """Fit local terms through quartic order around the ion location."""
    dx, dy, values = _local_points(field, x_um, y_um, ion, radius_um)
    if values.size < 15:
        return {}
    scale = max(radius_um, 1.0)
    xs = dx / scale
    ys = dy / scale
    cols = [
        np.ones_like(xs),
        xs,
        ys,
        xs**2,
        xs * ys,
        ys**2,
        xs**3,
        xs**2 * ys,
        xs * ys**2,
        ys**3,
        xs**4,
        xs**3 * ys,
        xs**2 * ys**2,
        xs * ys**3,
        ys**4,
    ]
    names = [
        "c0",
        "x",
        "y",
        "x2",
        "xy",
        "y2",
        "x3",
        "x2y",
        "xy2",
        "y3",
        "x4",
        "x3y",
        "x2y2",
        "xy3",
        "y4",
    ]
    coeffs, *_ = np.linalg.lstsq(np.vstack(cols).T, values, rcond=None)
    return {name: float(coeff) for name, coeff in zip(names, coeffs)}


def secular_frequency_metrics(
    pseudopotential_micro_ev: np.ndarray,
    x_um: np.ndarray,
    y_um: np.ndarray,
    ion_mass_amu: float,
    ion: tuple[float, float] = (0.0, 0.0),
    radius_um: float = 60.0,
) -> SecularFrequencyMetrics | None:
    coeffs = fit_local_polynomial(pseudopotential_micro_ev, x_um, y_um, ion=ion, radius_um=radius_um)
    if not coeffs:
        return None
    scale = max(radius_um, 1.0)
    # Fit used normalized coordinates x/scale, y/scale, so convert the quadratic
    # coefficients back to micro-eV / um^2 before building the Hessian.
    a = coeffs.get("x2", 0.0) / scale**2
    b = coeffs.get("xy", 0.0) / scale**2
    c = coeffs.get("y2", 0.0) / scale**2
    h_micro_ev_um2 = np.array([[2.0 * a, b], [b, 2.0 * c]], dtype=float)
    h_j_m2 = h_micro_ev_um2 * MICRO_EV_TO_J * UM2_TO_M2_INV
    evals, evecs = np.linalg.eigh(h_j_m2)
    evals = np.maximum(evals, 0.0)
    mass_kg = ion_mass_amu * ATOMIC_MASS
    omega = np.sqrt(evals / mass_kg)
    freqs = omega / (2.0 * np.pi)
    axes = tuple(float(math.degrees(math.atan2(evecs[1, i], evecs[0, i]))) for i in range(2))
    return SecularFrequencyMetrics(
        omega_rad_s=(float(omega[0]), float(omega[1])),
        frequency_hz=(float(freqs[0]), float(freqs[1])),
        principal_axes_deg=(axes[0], axes[1]),
    )


def harmonicity_metrics(
    pseudopotential_micro_ev: np.ndarray,
    x_um: np.ndarray,
    y_um: np.ndarray,
    ion: tuple[float, float] = (0.0, 0.0),
    radius_um: float = 80.0,
) -> HarmonicityMetrics | None:
    coeffs = fit_local_polynomial(pseudopotential_micro_ev, x_um, y_um, ion=ion, radius_um=radius_um)
    if not coeffs:
        return None
    quad = math.sqrt(coeffs.get("x2", 0.0) ** 2 + coeffs.get("xy", 0.0) ** 2 + coeffs.get("y2", 0.0) ** 2)
    quartic = math.sqrt(
        coeffs.get("x4", 0.0) ** 2
        + coeffs.get("x3y", 0.0) ** 2
        + coeffs.get("x2y2", 0.0) ** 2
        + coeffs.get("xy3", 0.0) ** 2
        + coeffs.get("y4", 0.0) ** 2
    )
    return HarmonicityMetrics(
        quartic_to_quadratic=float(quartic / max(quad, 1.0e-15)),
        fit_radius_um=float(radius_um),
    )


def derived_metrics(
    pseudopotential_micro_ev: np.ndarray,
    x_um: np.ndarray,
    y_um: np.ndarray,
    ion_mass_amu: float,
    ion: tuple[float, float] = (0.0, 0.0),
) -> DerivedMetrics:
    return DerivedMetrics(
        secular=secular_frequency_metrics(pseudopotential_micro_ev, x_um, y_um, ion_mass_amu=ion_mass_amu, ion=ion),
        harmonicity=harmonicity_metrics(pseudopotential_micro_ev, x_um, y_um, ion=ion),
    )
