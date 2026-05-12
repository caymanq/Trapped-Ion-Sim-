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
    outline: list[tuple[float, float]] | None = None


class UChannelParameters(BaseModel):
    opening_width: float = Field(default=180.0, gt=10.0)
    blade_height: float = Field(default=260.0, gt=10.0)
    blade_thickness: float = Field(default=70.0, gt=5.0)
    gap_to_ion: float = Field(default=70.0, ge=0.0)
    bezier_curvature: float = Field(default=0.35, ge=0.0, le=1.0)
    blade_angle_deg: float = Field(default=8.0, ge=-45.0, le=45.0)
    rf_voltage: float = Field(default=1.0, gt=0.0)


class UChannelGeometry(BaseModel):
    parameters: UChannelParameters
    electrodes: list[Electrode]
    outlines: dict[str, list[tuple[float, float]]]


class SecularFrequencyMetrics(BaseModel):
    omega_rad_s: tuple[float, float]
    frequency_hz: tuple[float, float]
    principal_axes_deg: tuple[float, float]


class HarmonicityMetrics(BaseModel):
    quartic_to_quadratic: float
    fit_radius_um: float


class DerivedMetrics(BaseModel):
    secular: SecularFrequencyMetrics | None = None
    harmonicity: HarmonicityMetrics | None = None


class SweepRequest(BaseModel):
    base: UChannelParameters = Field(default_factory=UChannelParameters)
    parameter: Literal[
        "opening_width",
        "blade_height",
        "blade_thickness",
        "gap_to_ion",
        "bezier_curvature",
        "blade_angle_deg",
        "rf_voltage",
    ] = "opening_width"
    values: list[float] = Field(default_factory=lambda: [140.0, 180.0, 220.0])
    grid_size: int = Field(default=61, ge=41, le=401)
    domain_um: float = Field(default=500.0, gt=20.0)


class SweepPoint(BaseModel):
    parameter_value: float
    trap_depth_micro_ev: float
    multipole_ratios: dict[str, float]
    metrics: DerivedMetrics
    warnings: list[str] = []


class SweepResponse(BaseModel):
    parameter: str
    points: list[SweepPoint]


class GeometryPreset(BaseModel):
    name: str
    parameters: UChannelParameters
    solver: SolverKind = "fd"
    domain_um: float = Field(default=500.0, gt=20.0)
    grid_size: int = Field(default=121, ge=41, le=401)
    rf_voltage: float = Field(default=500.0, gt=0.0)
    rf_frequency_hz: float = Field(default=30.0e6, gt=0.0)
    ion_mass_amu: float = Field(default=9.0121831, gt=0.0)


class TrapPreset(BaseModel):
    id: str
    name: str
    description: str
    ion: tuple[float, float] = (0.0, 0.0)
    electrodes: list[Electrode]


class SimulationRequest(BaseModel):
    preset_id: str | None = None
    electrodes: list[Electrode] | None = None
    u_channel: UChannelParameters | None = None
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
    metrics: DerivedMetrics = Field(default_factory=DerivedMetrics)
    validation: ValidationResult
    warnings: list[str] = []
