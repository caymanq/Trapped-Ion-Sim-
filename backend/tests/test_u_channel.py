import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from iontrap.fd_solver import make_grid
from iontrap.geometry import electrode_mask
from iontrap.metrics import derived_metrics
from iontrap.models import GeometryPreset, SimulationRequest, SweepRequest, UChannelParameters
from iontrap.presets import preset_from_json, preset_to_json
from iontrap.simulation import simulate_trap
from iontrap.sweeps import run_u_channel_sweep
from iontrap.u_channel import generate_u_channel, rasterize_u_channel


def test_u_channel_generator_returns_symmetric_outlines():
    params = UChannelParameters(opening_width=180.0, blade_height=240.0, blade_thickness=60.0, gap_to_ion=50.0)
    geometry = generate_u_channel(params)
    assert len(geometry.electrodes) == 2
    assert set(geometry.outlines) == {"u_left_rf", "u_right_rf"}
    left = geometry.electrodes[0]
    right = geometry.electrodes[1]
    assert left.outline
    assert right.outline
    assert left.cx < 0 < right.cx
    assert np.isclose(abs(left.cx), abs(right.cx), rtol=0.08)


def test_u_channel_masks_are_non_empty_and_change_with_opening():
    x, y, X, Y = make_grid(500.0, 101)
    narrow = UChannelParameters(opening_width=120.0)
    wide = UChannelParameters(opening_width=260.0)
    narrow_electrodes, narrow_masks = rasterize_u_channel(narrow, X, Y)
    wide_electrodes, wide_masks = rasterize_u_channel(wide, X, Y)
    assert all(mask.any() for mask in narrow_masks)
    assert all(mask.any() for mask in wide_masks)
    assert abs(wide_electrodes[0].cx) > abs(narrow_electrodes[0].cx)
    assert electrode_mask(narrow_electrodes[0], X, Y).sum() > 0


def test_u_channel_simulation_returns_metrics():
    result = simulate_trap(SimulationRequest(u_channel=UChannelParameters(), grid_size=61))
    assert len(result.electrodes) == 2
    assert result.trap_depth_micro_ev >= 0.0
    assert result.metrics.harmonicity is not None
    assert result.metrics.harmonicity.quartic_to_quadratic >= 0.0
    assert result.metrics.secular is not None
    assert len(result.metrics.secular.frequency_hz) == 2


def test_sweep_and_preset_round_trip():
    params = UChannelParameters(opening_width=180.0)
    sweep = run_u_channel_sweep(SweepRequest(base=params, values=[160.0, 180.0], grid_size=41))
    assert sweep.parameter == "opening_width"
    assert [point.parameter_value for point in sweep.points] == [160.0, 180.0]

    preset = GeometryPreset(name="test-u", parameters=params)
    encoded = preset_to_json(preset)
    decoded = preset_from_json(encoded)
    assert decoded.name == preset.name
    assert decoded.parameters.opening_width == params.opening_width


def test_synthetic_quadratic_well_metrics_are_finite():
    x = np.linspace(-100.0, 100.0, 81)
    y = np.linspace(-100.0, 100.0, 81)
    X, Y = np.meshgrid(x, y)
    pseudo = 0.02 * X**2 + 0.03 * Y**2 + 1.0e-8 * X**4
    metrics = derived_metrics(pseudo, x, y, ion_mass_amu=9.0121831)
    assert metrics.secular is not None
    assert all(freq >= 0.0 for freq in metrics.secular.frequency_hz)
    assert metrics.harmonicity is not None
    assert metrics.harmonicity.quartic_to_quadratic >= 0.0
