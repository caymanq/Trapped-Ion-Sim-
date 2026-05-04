"""RF pseudopotential and trap-depth calculations."""

from __future__ import annotations

import numpy as np

from .constants import ATOMIC_MASS, ELEMENTARY_CHARGE


def compute_pseudopotential_micro_ev(
    rf_potential: np.ndarray,
    x_um: np.ndarray,
    y_um: np.ndarray,
    rf_voltage: float,
    rf_frequency_hz: float,
    ion_mass_amu: float,
) -> np.ndarray:
    """Return RF pseudopotential in micro electron-volts.

    The solved RF field is dimensionless for a 1 V electrode basis. It is scaled
    by the requested RF voltage before applying q^2 |E|^2 / (4 m Omega^2).
    """
    omega = 2.0 * np.pi * rf_frequency_hz
    mass_kg = ion_mass_amu * ATOMIC_MASS
    gy, gx = np.gradient(rf_potential, y_um * 1.0e-6, x_um * 1.0e-6, edge_order=2)
    electric_field2 = (rf_voltage * gx) ** 2 + (rf_voltage * gy) ** 2
    energy_j = (ELEMENTARY_CHARGE**2 * electric_field2) / (4.0 * mass_kg * omega**2)
    energy_ev = energy_j / ELEMENTARY_CHARGE
    return energy_ev * 1.0e6


def trap_depth_micro_ev(
    pseudopotential_micro_ev: np.ndarray,
    x_um: np.ndarray,
    y_um: np.ndarray,
    ion: tuple[float, float] = (0.0, 0.0),
    radius_um: float | None = None,
) -> float:
    """Estimate trap depth as the barrier above the pseudopotential at the ion."""
    ix = int(np.argmin(np.abs(x_um - ion[0])))
    iy = int(np.argmin(np.abs(y_um - ion[1])))
    floor = float(pseudopotential_micro_ev[iy, ix])
    if radius_um is None:
        radius_um = min(float(np.max(np.abs(x_um))), float(np.max(np.abs(y_um)))) * 0.35
    X, Y = np.meshgrid(x_um, y_um)
    r = np.hypot(X - ion[0], Y - ion[1])
    search = pseudopotential_micro_ev[r <= radius_um]
    if search.size == 0:
        return 0.0
    return max(0.0, float(np.nanmax(search) - floor))
