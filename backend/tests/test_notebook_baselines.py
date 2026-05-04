import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from iontrap.geometry import list_presets
from iontrap.models import SimulationRequest
from iontrap.simulation import simulate_trap


ROOT = Path(__file__).resolve().parents[2]


def _csv_rows(name: str) -> list[str]:
    with (ROOT / "csv" / name).open(newline="") as handle:
        reader = csv.reader(handle)
        next(reader)
        return [row[0] for row in reader]


def test_notebook_csv_baselines_cover_all_presets():
    preset_names = [preset.name for preset in list_presets()]
    assert _csv_rows("sim_rf_ratios.csv") == preset_names
    assert _csv_rows("bem_rf_ratios.csv") == preset_names


def test_api_response_contains_notebook_baseline_diagnostics():
    result = simulate_trap(SimulationRequest(preset_id="f", grid_size=61))
    assert set(result.multipole_ratios) == {"p3/p2", "p4/p2", "p5/p2", "p6/p2", "p7/p2", "p8/p2"}
    assert result.trap_depth_micro_ev >= 0
    assert result.validation.laplace_bulk_passed
