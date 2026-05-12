export type Electrode = {
  id: string;
  label: string;
  kind: "RF" | "RF+" | "RF-" | "DC" | "GND";
  cx: number;
  cy: number;
  width: number;
  height: number;
  voltage: number;
  curvature: number;
  outline?: [number, number][] | null;
};

export type UChannelParameters = {
  opening_width: number;
  blade_height: number;
  blade_thickness: number;
  gap_to_ion: number;
  bezier_curvature: number;
  blade_angle_deg: number;
  rf_voltage: number;
};

export type TrapPreset = {
  id: string;
  name: string;
  description: string;
  ion: [number, number];
  electrodes: Electrode[];
};

export type SimulationResponse = {
  solver: "fd" | "bem";
  electrodes: Electrode[];
  x_um: number[];
  y_um: number[];
  potential: number[][];
  pseudopotential_micro_ev: number[][];
  rf_null_um: [number, number];
  trap_depth_micro_ev: number;
  multipole_ratios: Record<string, number>;
  metrics: {
    secular?: {
      omega_rad_s: [number, number];
      frequency_hz: [number, number];
      principal_axes_deg: [number, number];
    } | null;
    harmonicity?: {
      quartic_to_quadratic: number;
      fit_radius_um: number;
    } | null;
  };
  validation: {
    laplace_passed: boolean;
    laplace_bulk_passed: boolean;
    electrode_voltage_passed: boolean;
    normalised_laplace_max: number;
    normalised_laplace_bulk_max: number;
    electrode_voltage_max_relative_error: number;
    all_passed: boolean;
    warnings: string[];
  };
  warnings: string[];
};

const API_BASE = process.env.NEXT_PUBLIC_ION_TRAP_API_URL ?? "http://localhost:8000";

export async function getTraps(): Promise<TrapPreset[]> {
  const response = await fetch(`${API_BASE}/traps`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load traps: ${response.statusText}`);
  }
  return response.json();
}

export async function simulateTrap(input: {
  preset_id?: string;
  electrodes?: Electrode[];
  u_channel?: UChannelParameters;
  solver: "fd" | "bem";
  hyperbolic_slider: number;
  grid_size: number;
}): Promise<SimulationResponse> {
  const response = await fetch(`${API_BASE}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) {
    throw new Error(`Simulation failed: ${response.statusText}`);
  }
  return response.json();
}

export async function sweepUChannel(input: {
  base: UChannelParameters;
  parameter: keyof UChannelParameters;
  values: number[];
  grid_size: number;
  domain_um?: number;
}): Promise<{
  parameter: string;
  points: {
    parameter_value: number;
    trap_depth_micro_ev: number;
    multipole_ratios: Record<string, number>;
    metrics: SimulationResponse["metrics"];
    warnings: string[];
  }[];
}> {
  const response = await fetch(`${API_BASE}/u-channel/sweep`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });
  if (!response.ok) {
    throw new Error(`Sweep failed: ${response.statusText}`);
  }
  return response.json();
}
