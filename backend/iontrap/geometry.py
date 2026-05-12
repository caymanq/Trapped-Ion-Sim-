"""Trap geometry presets and electrode rasterisation.

All trap presets use the notebook convention: the ion/RF null is at
``(x, y) = (0, 0)``, x is horizontal, and y is vertical.
"""

from __future__ import annotations

import numpy as np

from .models import Electrode, TrapPreset


def _e(id_: str, label: str, kind: str, cx: float, cy: float, width: float, height: float, voltage: float) -> Electrode:
    return Electrode(id=id_, label=label, kind=kind, cx=cx, cy=cy, width=width, height=height, voltage=voltage)


def trap_a_2layer() -> TrapPreset:
    hgap, ew = 200.0, 125.0
    left, right = -hgap / 2.0 - ew / 2.0, hgap / 2.0 + ew / 2.0
    return TrapPreset(
        id="a",
        name="(a) 2-layer",
        description="Two-layer trap with central free region x=[-100,100], y=[-100,100].",
        electrodes=[
            _e("a_rf_minus_top", "RF-", "RF-", left, 162.5, ew, 125.0, -1.0),
            _e("a_rf_plus_top", "RF+", "RF+", right, 162.5, ew, 125.0, 1.0),
            _e("a_rf_plus_bottom", "RF+", "RF+", left, -162.5, ew, 125.0, 1.0),
            _e("a_rf_minus_bottom", "RF-", "RF-", right, -162.5, ew, 125.0, -1.0),
        ],
    )


def trap_b_balanced() -> TrapPreset:
    hgap, ew = 200.0, 125.0
    left, right = -hgap / 2.0 - ew / 2.0, hgap / 2.0 + ew / 2.0
    return TrapPreset(
        id="b",
        name="(b) Balanced 2-layer",
        description="Two-layer trap with 220 um vertical gap and 125 um lower electrode height.",
        electrodes=[
            _e("b_rf_minus_top", "RF-", "RF-", left, 172.5, ew, 125.0, -1.0),
            _e("b_rf_plus_top", "RF+", "RF+", right, 172.5, ew, 125.0, 1.0),
            _e("b_rf_plus_bottom", "RF+", "RF+", left, -172.5, ew, 125.0, 1.0),
            _e("b_rf_minus_bottom", "RF-", "RF-", right, -172.5, ew, 125.0, -1.0),
        ],
    )


def trap_c_3layer() -> TrapPreset:
    hgap, ew = 200.0, 125.0
    left, right = -hgap / 2.0 - ew / 2.0, hgap / 2.0 + ew / 2.0
    return TrapPreset(
        id="c",
        name="(c) 3-layer",
        description="Three-layer trap with RF y=[-62.5,62.5] and DC layers above/below.",
        electrodes=[
            _e("c_dc_left_top", "DC", "DC", left, 312.5, ew, 250.0, 1.0),
            _e("c_dc_right_top", "DC", "DC", right, 312.5, ew, 250.0, 1.0),
            _e("c_rf_left", "RF", "RF", left, 0.0, ew, 125.0, -1.0),
            _e("c_rf_right", "RF", "RF", right, 0.0, ew, 125.0, -1.0),
            _e("c_dc_left_bottom", "DC", "DC", left, -312.5, ew, 250.0, 1.0),
            _e("c_dc_right_bottom", "DC", "DC", right, -312.5, ew, 250.0, 1.0),
        ],
    )


def trap_d_algaas() -> TrapPreset:
    ew, stack_w = 80.0, 2.3
    left, right = -30.0 - ew / 2.0, 30.0 + ew / 2.0
    return TrapPreset(
        id="d",
        name="(d) 2-layer AlGaAs",
        description="Thin asymmetric AlGaAs-style side stacks with 60 um horizontal gap.",
        electrodes=[
            _e("d_left_upper", "RF+", "RF+", left, 3.15, ew, stack_w, 1.0),
            _e("d_right_upper", "RF-", "RF-", right, 3.15, ew, stack_w, -1.0),
            _e("d_left_lower", "RF-", "RF-", left, -3.15, ew, stack_w, -1.0),
            _e("d_right_lower", "RF+", "RF+", right, -3.15, ew, stack_w, 1.0),
        ],
    )


def trap_e_inplane4() -> TrapPreset:
    return TrapPreset(
        id="e",
        name="(e) In-plane 4-wire",
        description="In-plane four-wire trap with inner red electrodes at x=[-60,-40] and [40,60].",
        electrodes=[
            _e("e_left_outer", "GND", "GND", -110.0, 0.0, 100.0, 20.0, 0.0),
            _e("e_left_inner", "RF", "RF", -50.0, 0.0, 20.0, 20.0, 1.0),
            _e("e_right_inner", "RF", "RF", 50.0, 0.0, 20.0, 20.0, -1.0),
            _e("e_right_outer", "GND", "GND", 110.0, 0.0, 100.0, 20.0, 0.0),
        ],
    )


def trap_f_4wire_surface() -> TrapPreset:
    return TrapPreset(
        id="f",
        name="(f) 4-wire surface",
        description="Surface trap with electrode plane y=-40 and boundaries x=-40,0,40.",
        electrodes=[
            _e("f_left_outer", "GND", "GND", -120.0, -40.0, 160.0, 20.0, 0.0),
            _e("f_left_inner", "RF", "RF", -20.0, -40.0, 40.0, 20.0, 1.0),
            _e("f_right_inner", "GND", "GND", 20.0, -40.0, 40.0, 20.0, 0.0),
            _e("f_right_outer", "RF", "RF", 120.0, -40.0, 160.0, 20.0, -1.0),
        ],
    )


def trap_g_5wire_symm() -> TrapPreset:
    return TrapPreset(
        id="g",
        name="(g) 5-wire symm. surface",
        description="Symmetric five-wire surface trap with inner boundaries x=-60,-20,20,60.",
        electrodes=[
            _e("g_left_outer", "GND", "GND", -130.0, -40.0, 140.0, 20.0, 0.0),
            _e("g_left_inner", "RF", "RF", -40.0, -40.0, 40.0, 20.0, 1.0),
            _e("g_center", "GND", "GND", 0.0, -40.0, 40.0, 20.0, 0.0),
            _e("g_right_inner", "RF", "RF", 40.0, -40.0, 40.0, 20.0, -1.0),
            _e("g_right_outer", "GND", "GND", 130.0, -40.0, 140.0, 20.0, 0.0),
        ],
    )


def trap_h_5wire_asymm() -> TrapPreset:
    return TrapPreset(
        id="h",
        name="(h) 5-wire asymm. surface",
        description="Asymmetric five-wire surface trap with inner boundaries x=-60,-16,24,60.",
        electrodes=[
            _e("h_left_outer", "GND", "GND", -130.0, -40.0, 140.0, 20.0, 0.0),
            _e("h_left_inner", "RF", "RF", -38.0, -40.0, 44.0, 20.0, 1.0),
            _e("h_center", "GND", "GND", 4.0, -40.0, 40.0, 20.0, 0.0),
            _e("h_right_inner", "RF", "RF", 42.0, -40.0, 36.0, 20.0, -1.0),
            _e("h_right_outer", "GND", "GND", 130.0, -40.0, 140.0, 20.0, 0.0),
        ],
    )


PRESET_BUILDERS = {
    "a": trap_a_2layer,
    "b": trap_b_balanced,
    "c": trap_c_3layer,
    "d": trap_d_algaas,
    "e": trap_e_inplane4,
    "f": trap_f_4wire_surface,
    "g": trap_g_5wire_symm,
    "h": trap_h_5wire_asymm,
}


def list_presets() -> list[TrapPreset]:
    return [builder() for builder in PRESET_BUILDERS.values()]


def get_preset(preset_id: str) -> TrapPreset:
    try:
        return PRESET_BUILDERS[preset_id.lower()]()
    except KeyError as exc:
        raise ValueError(f"Unknown trap preset: {preset_id}") from exc


def apply_hyperbolic_slider(electrodes: list[Electrode], slider: float) -> list[Electrode]:
    """Return copies with curvature set by the UI slider."""
    return [electrode.model_copy(update={"curvature": max(electrode.curvature, slider)}) for electrode in electrodes]


def electrode_mask(electrode: Electrode, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Rasterise rectangular or mildly hyperbolic electrodes onto a meshgrid."""
    x_rel = x - electrode.cx
    y_rel = y - electrode.cy
    half_h = electrode.height / 2.0
    inside_y = np.abs(y_rel) <= half_h
    eta = np.zeros_like(y_rel, dtype=float)
    if half_h > 0:
        eta = np.clip(y_rel / half_h, -1.0, 1.0)

    half_w = electrode.width / 2.0
    curve = np.clip(electrode.curvature, 0.0, 1.0)
    # Convex sidewall protrusion toward the trap centre (RF null): widen the
    # conductor at mid-height so each vertical boundary bows toward x=0, with
    # corners fixed at η=±1—mirrors hyperbolic electrodes whose tip points inward.
    local_half_w = half_w * (1.0 + 0.35 * curve * (1.0 - eta**2))
    mask = inside_y & (np.abs(x_rel) <= local_half_w)
    if not mask.any():
        # Thin electrodes can disappear on coarse grids. Pin them to the nearest
        # grid row/column so voltage validation remains meaningful.
        ix = np.argmin(np.abs(x[0, :] - electrode.cx))
        iy = np.argmin(np.abs(y[:, 0] - electrode.cy))
        x_span = np.abs(x[0, :] - electrode.cx) <= max(half_w, np.diff(x[0, :]).mean() / 2.0)
        y_span = np.abs(y[:, 0] - electrode.cy) <= max(half_h, np.diff(y[:, 0]).mean() / 2.0)
        mask[np.ix_(y_span, x_span)] = True
        mask[iy, ix] = True
    return mask
