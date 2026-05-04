"""Shared request and response models for the compute API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ElectrodeKind = Literal["RF", "RF+", "RF-", "DC", "GND"]
SolverKind = Literal["fd", "bem"]


class Electrode(BaseModel):
    id: str
    label: str
    kind: ElectrodeKind = "RF"
    cx: float
    cy: float
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    voltage: float
    curvature: float = Field(default=0.0, ge=0.0, le=1.0)


class TrapPreset(BaseModel):
    id: str
    name: str
    description: str
    ion: tuple[float, float] = (0.0, 0.0)
    electrodes: list[Electrode]


class SimulationRequest(BaseModel):
    preset_id: str | None = None
    electrodes: list[Electrode] | None = None
    solver: SolverKind = "fd"
    domain_um: float = Field(default=500.0, gt=20.0)
    grid_size: int = Field(default=121, ge=41, le=401)
    hyperbolic_slider: float = Field(default=0.0, ge=0.0, le=1.0)
    rf_voltage: float = Field(default=500.0, gt=0.0)
    rf_frequency_hz: float = Field(default=30.0e6, gt=0.0)
    ion_mass_amu: float = Field(default=9.0121831, gt=0.0)


class ValidationResult(BaseModel):
    laplace_passed: bool
    laplace_bulk_passed: bool
    electrode_voltage_passed: bool
    normalised_laplace_max: float
    normalised_laplace_bulk_max: float
    electrode_voltage_max_relative_error: float
    all_passed: bool
    warnings: list[str] = []


class SimulationResponse(BaseModel):
    solver: SolverKind
    electrodes: list[Electrode]
    x_um: list[float]
    y_um: list[float]
    potential: list[list[float]]
    pseudopotential_micro_ev: list[list[float]]
    rf_null_um: tuple[float, float]
    trap_depth_micro_ev: float
    multipole_ratios: dict[str, float]
    validation: ValidationResult
    warnings: list[str] = []
