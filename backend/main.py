"""FastAPI compute service for the ion-trap website."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from iontrap.geometry import list_presets
from iontrap.models import (
    GeometryPreset,
    SimulationRequest,
    SimulationResponse,
    SweepRequest,
    SweepResponse,
    TrapPreset,
    UChannelGeometry,
    UChannelParameters,
)
from iontrap.presets import preset_from_json, preset_to_dict
from iontrap.simulation import simulate_trap
from iontrap.sweeps import run_u_channel_sweep
from iontrap.u_channel import generate_u_channel

app = FastAPI(title="Ion Trap Compute API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/traps", response_model=list[TrapPreset])
def traps() -> list[TrapPreset]:
    return list_presets()


@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest) -> SimulationResponse:
    return simulate_trap(request)


@app.post("/validate", response_model=SimulationResponse)
def validate(request: SimulationRequest) -> SimulationResponse:
    return simulate_trap(request)


@app.post("/u-channel/geometry", response_model=UChannelGeometry)
def u_channel_geometry(request: UChannelParameters) -> UChannelGeometry:
    return generate_u_channel(request)


@app.post("/u-channel/sweep", response_model=SweepResponse)
def u_channel_sweep(request: SweepRequest) -> SweepResponse:
    return run_u_channel_sweep(request)


@app.post("/presets/parse")
def parse_preset(preset_json: str) -> dict:
    return preset_to_dict(preset_from_json(preset_json))


@app.post("/presets/normalise")
def normalise_preset(preset: GeometryPreset) -> dict:
    return preset_to_dict(preset)
