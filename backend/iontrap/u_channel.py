"""Parametric U-channel blade-trap geometry generation."""

from __future__ import annotations

import math

import numpy as np

from .geometry import electrode_mask
from .models import Electrode, UChannelGeometry, UChannelParameters


def _quadratic_bezier(
    start: tuple[float, float],
    control: tuple[float, float],
    end: tuple[float, float],
    samples: int = 24,
) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for t in np.linspace(0.0, 1.0, samples):
        u = 1.0 - t
        x = u * u * start[0] + 2.0 * u * t * control[0] + t * t * end[0]
        y = u * u * start[1] + 2.0 * u * t * control[1] + t * t * end[1]
        points.append((float(x), float(y)))
    return points


def _bounds(outline: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    return min(xs), max(xs), min(ys), max(ys)


def _electrode_from_outline(id_: str, label: str, kind: str, voltage: float, outline: list[tuple[float, float]]) -> Electrode:
    x0, x1, y0, y1 = _bounds(outline)
    return Electrode(
        id=id_,
        label=label,
        kind=kind,
        cx=(x0 + x1) / 2.0,
        cy=(y0 + y1) / 2.0,
        width=max(x1 - x0, 1.0e-6),
        height=max(y1 - y0, 1.0e-6),
        voltage=voltage,
        curvature=0.0,
        outline=outline,
    )


def _blade_outline(params: UChannelParameters, side: int) -> list[tuple[float, float]]:
    """Return one side blade polygon.

    ``side`` is -1 for the left blade and +1 for the right blade. The U opens
    upward: blade tips are near the ion and blade bodies extend toward negative y.
    """
    half_open = params.opening_width / 2.0
    tip_y = -params.gap_to_ion
    base_y = tip_y - params.blade_height
    flare = math.tan(math.radians(params.blade_angle_deg)) * params.blade_height
    inner_tip_x = side * half_open
    inner_base_x = side * (half_open + flare)
    outer_tip_x = inner_tip_x + side * params.blade_thickness
    outer_base_x = inner_base_x + side * params.blade_thickness
    curve = side * params.bezier_curvature * params.blade_thickness

    inner = _quadratic_bezier(
        (inner_tip_x, tip_y),
        ((inner_tip_x + inner_base_x) / 2.0 - curve, (tip_y + base_y) / 2.0),
        (inner_base_x, base_y),
    )
    outer = _quadratic_bezier(
        (outer_base_x, base_y),
        ((outer_tip_x + outer_base_x) / 2.0, (tip_y + base_y) / 2.0),
        (outer_tip_x, tip_y),
    )
    return inner + outer


def generate_u_channel(params: UChannelParameters | None = None) -> UChannelGeometry:
    """Generate symmetric Bezier-approximated U-channel RF blade electrodes."""
    params = params or UChannelParameters()
    left = _blade_outline(params, side=-1)
    right = _blade_outline(params, side=1)
    electrodes = [
        _electrode_from_outline("u_left_rf", "Left RF blade", "RF+", params.rf_voltage, left),
        _electrode_from_outline("u_right_rf", "Right RF blade", "RF-", -params.rf_voltage, right),
    ]
    return UChannelGeometry(
        parameters=params,
        electrodes=electrodes,
        outlines={electrode.id: electrode.outline or [] for electrode in electrodes},
    )


def rasterize_u_channel(
    params: UChannelParameters,
    x: np.ndarray,
    y: np.ndarray,
) -> tuple[list[Electrode], list[np.ndarray]]:
    geometry = generate_u_channel(params)
    masks = [electrode_mask(electrode, x, y) for electrode in geometry.electrodes]
    return geometry.electrodes, masks
