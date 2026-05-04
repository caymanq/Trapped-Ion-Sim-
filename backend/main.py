"""FastAPI compute service for the ion-trap website."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from iontrap.geometry import list_presets
from iontrap.models import SimulationRequest, SimulationResponse, TrapPreset
from iontrap.simulation import simulate_trap

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
