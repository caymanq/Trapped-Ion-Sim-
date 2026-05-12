"""High-level simulation orchestration used by the FastAPI app."""

from __future__ import annotations

from .bem_solver import solve_laplace_bem
from .constants import DEFAULT_DOMAIN_UM, DEFAULT_GRID_SIZE
from .fd_solver import solve_laplace_fd
from .geometry import apply_hyperbolic_slider, get_preset
from .metrics import derived_metrics
from .models import Electrode, SimulationRequest, SimulationResponse
from .multipole import fit_multipole_ratios
from .pseudopotential import compute_pseudopotential_micro_ev, trap_depth_micro_ev
from .validation import validate_solution


def _resolve_electrodes(request: SimulationRequest) -> list[Electrode]:
    if request.u_channel:
        from .u_channel import generate_u_channel

        return generate_u_channel(request.u_channel).electrodes
    if request.electrodes:
        return request.electrodes
    if request.preset_id:
        return get_preset(request.preset_id).electrodes
    return get_preset("a").electrodes


def simulate_trap(request: SimulationRequest) -> SimulationResponse:
    electrodes = apply_hyperbolic_slider(_resolve_electrodes(request), request.hyperbolic_slider)
    domain_um = request.domain_um or DEFAULT_DOMAIN_UM
    grid_size = request.grid_size or DEFAULT_GRID_SIZE

    solver = solve_laplace_bem if request.solver == "bem" else solve_laplace_fd
    potential, x_um, y_um, X, Y, fixed, _masks = solver(electrodes, domain_um=domain_um, grid_size=grid_size)

    pseudo = compute_pseudopotential_micro_ev(
        potential,
        x_um,
        y_um,
        rf_voltage=request.rf_voltage,
        rf_frequency_hz=request.rf_frequency_hz,
        ion_mass_amu=request.ion_mass_amu,
    )
    depth = trap_depth_micro_ev(pseudo, x_um, y_um, ion=(0.0, 0.0))
    multipole_ratios = fit_multipole_ratios(pseudo, x_um, y_um, ion=(0.0, 0.0))
    metrics = derived_metrics(pseudo, x_um, y_um, ion_mass_amu=request.ion_mass_amu, ion=(0.0, 0.0))
    validation = validate_solution(potential, x_um, y_um, X, Y, electrodes, fixed)

    warnings = list(validation.warnings)
    return SimulationResponse(
        solver=request.solver,
        electrodes=electrodes,
        x_um=[float(v) for v in x_um],
        y_um=[float(v) for v in y_um],
        potential=potential.tolist(),
        pseudopotential_micro_ev=pseudo.tolist(),
        rf_null_um=(0.0, 0.0),
        trap_depth_micro_ev=depth,
        multipole_ratios=multipole_ratios,
        metrics=metrics,
        validation=validation,
        warnings=warnings,
    )
