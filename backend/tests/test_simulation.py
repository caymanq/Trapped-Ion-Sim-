import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from iontrap.geometry import list_presets
from iontrap.models import SimulationRequest
from iontrap.simulation import simulate_trap
from main import app


def test_all_eight_presets_are_available():
    presets = list_presets()
    assert [preset.id for preset in presets] == list("abcdefgh")
    assert all(preset.electrodes for preset in presets)


def test_fd_simulation_returns_depth_and_validation():
    result = simulate_trap(SimulationRequest(preset_id="a", grid_size=61))
    assert result.trap_depth_micro_ev >= 0
    assert result.validation.laplace_bulk_passed
    assert result.validation.electrode_voltage_passed
    assert len(result.potential) == 61
    assert len(result.pseudopotential_micro_ev) == 61


def test_hyperbolic_slider_updates_electrode_curvature():
    result = simulate_trap(SimulationRequest(preset_id="g", grid_size=61, hyperbolic_slider=0.5))
    assert all(electrode.curvature >= 0.5 for electrode in result.electrodes)


def test_bem_simulation_mode_returns_grid():
    result = simulate_trap(SimulationRequest(preset_id="a", solver="bem", grid_size=41))
    assert result.solver == "bem"
    assert len(result.potential) == 41
    assert result.validation.electrode_voltage_passed


def test_api_traps_and_simulate_endpoints():
    client = TestClient(app)
    traps = client.get("/traps")
    assert traps.status_code == 200
    assert len(traps.json()) == 8

    simulation = client.post("/simulate", json={"preset_id": "f", "grid_size": 61, "hyperbolic_slider": 0.25})
    assert simulation.status_code == 200
    payload = simulation.json()
    assert payload["trap_depth_micro_ev"] >= 0
    assert payload["validation"]["laplace_bulk_passed"]
