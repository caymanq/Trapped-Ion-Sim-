"""Parameter sweeps for U-channel trap exploration."""

from __future__ import annotations

from .models import SimulationRequest, SweepPoint, SweepRequest, SweepResponse
from .simulation import simulate_trap


def run_u_channel_sweep(request: SweepRequest) -> SweepResponse:
    points: list[SweepPoint] = []
    for value in request.values:
        params = request.base.model_copy(update={request.parameter: value})
        simulation = simulate_trap(
            SimulationRequest(
                u_channel=params,
                solver="fd",
                domain_um=request.domain_um,
                grid_size=request.grid_size,
                rf_voltage=500.0,
            )
        )
        points.append(
            SweepPoint(
                parameter_value=float(value),
                trap_depth_micro_ev=simulation.trap_depth_micro_ev,
                multipole_ratios=simulation.multipole_ratios,
                metrics=simulation.metrics,
                warnings=simulation.warnings + simulation.validation.warnings,
            )
        )
    return SweepResponse(parameter=request.parameter, points=points)
