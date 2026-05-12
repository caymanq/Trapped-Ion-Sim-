"use client";

import { useEffect, useMemo, useState, type PointerEvent } from "react";
import { getTraps, simulateTrap, sweepUChannel, type Electrode, type SimulationResponse, type TrapPreset, type UChannelParameters } from "../lib/api";
import { PSEUDO_PANEL_HALF_WIDTH_UM, TrapPlots } from "./TrapPlots";

const DEFAULT_U_CHANNEL: UChannelParameters = {
  opening_width: 180,
  blade_height: 260,
  blade_thickness: 70,
  gap_to_ion: 70,
  bezier_curvature: 0.35,
  blade_angle_deg: 8,
  rf_voltage: 1
};

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function previewBladePath(params: UChannelParameters, side: -1 | 1, sx: (x: number) => number, sy: (y: number) => number) {
  const half = params.opening_width / 2;
  const tipY = -params.gap_to_ion;
  const baseY = tipY - params.blade_height;
  const flare = Math.tan((params.blade_angle_deg * Math.PI) / 180) * params.blade_height;
  const innerTipX = side * half;
  const innerBaseX = side * (half + flare);
  const outerTipX = innerTipX + side * params.blade_thickness;
  const outerBaseX = innerBaseX + side * params.blade_thickness;
  const curve = side * params.bezier_curvature * params.blade_thickness;
  const p = (x: number, y: number) => `${sx(x).toFixed(1)},${sy(y).toFixed(1)}`;
  return [
    `M ${p(innerTipX, tipY)}`,
    `Q ${p((innerTipX + innerBaseX) / 2 - curve, (tipY + baseY) / 2)} ${p(innerBaseX, baseY)}`,
    `L ${p(outerBaseX, baseY)}`,
    `Q ${p((outerTipX + outerBaseX) / 2, (tipY + baseY) / 2)} ${p(outerTipX, tipY)}`,
    "Z"
  ].join(" ");
}

function UChannelPreview({ params, onChange }: { params: UChannelParameters; onChange: (patch: Partial<UChannelParameters>) => void }) {
  const width = 320;
  const height = 220;
  const domainX = 360;
  const yMin = -380;
  const yMax = 80;
  const sx = (x: number) => ((x + domainX) / (2 * domainX)) * width;
  const sy = (y: number) => height - ((y - yMin) / (yMax - yMin)) * height;

  function pointerToWorld(event: PointerEvent<SVGSVGElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const px = ((event.clientX - rect.left) / rect.width) * width;
    const py = ((event.clientY - rect.top) / rect.height) * height;
    return {
      x: (px / width) * (2 * domainX) - domainX,
      y: yMin + (1 - py / height) * (yMax - yMin)
    };
  }

  return (
    <svg className="u-preview" viewBox={`0 0 ${width} ${height}`} onPointerMove={(event) => {
      if (event.buttons !== 1) return;
      const target = (event.target as SVGElement).dataset.handle;
      const world = pointerToWorld(event);
      if (target === "opening") {
        onChange({ opening_width: clamp(Math.abs(world.x) * 2, 40, 420) });
      } else if (target === "height") {
        onChange({ blade_height: clamp(-world.y - params.gap_to_ion, 40, 420) });
      }
    }}>
      <rect width={width} height={height} fill="#fff" />
      <line x1={sx(-domainX)} x2={sx(domainX)} y1={sy(0)} y2={sy(0)} stroke="#d62728" strokeWidth="1" />
      <line x1={sx(0)} x2={sx(0)} y1={sy(yMin)} y2={sy(yMax)} stroke="#d62728" strokeWidth="1" />
      <path d={previewBladePath(params, -1, sx, sy)} />
      <path d={previewBladePath(params, 1, sx, sy)} />
      <circle className="handle" data-handle="opening" cx={sx(params.opening_width / 2)} cy={sy(-params.gap_to_ion)} r="6" />
      <circle className="handle height" data-handle="height" cx={sx(0)} cy={sy(-params.gap_to_ion - params.blade_height)} r="6" />
      <text x="8" y="16" fontSize="11" fill="#555">drag blue handles: opening / blade height</text>
    </svg>
  );
}

function SweepTrend({ points }: { points: { parameter_value: number; trap_depth_micro_ev: number }[] }) {
  if (points.length < 2) return null;
  const width = 360;
  const height = 130;
  const pad = 28;
  const xs = points.map((p) => p.parameter_value);
  const ys = points.map((p) => p.trap_depth_micro_ev);
  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  const yMin = Math.min(...ys);
  const yMax = Math.max(...ys);
  const sx = (x: number) => pad + ((x - xMin) / Math.max(xMax - xMin, 1e-9)) * (width - 2 * pad);
  const sy = (y: number) => height - pad - ((y - yMin) / Math.max(yMax - yMin, 1e-9)) * (height - 2 * pad);
  const d = points.map((p, i) => `${i === 0 ? "M" : "L"} ${sx(p.parameter_value)},${sy(p.trap_depth_micro_ev)}`).join(" ");
  return (
    <div className="trend-wrap">
      <div className="figure-title">depth vs U-opening</div>
      <svg className="trend-svg" viewBox={`0 0 ${width} ${height}`}>
        <line x1={pad} x2={width - pad} y1={height - pad} y2={height - pad} stroke="#333" />
        <line x1={pad} x2={pad} y1={pad} y2={height - pad} stroke="#333" />
        <path d={d} fill="none" stroke="#1a5fb4" strokeWidth="2" />
        {points.map((p) => <circle key={p.parameter_value} cx={sx(p.parameter_value)} cy={sy(p.trap_depth_micro_ev)} r="3" fill="#1a5fb4" />)}
        <text x={width / 2} y={height - 5} textAnchor="middle" className="figure-axis-label">opening width (µm)</text>
        <text x="10" y="18" className="figure-axis-label">depth</text>
      </svg>
    </div>
  );
}

export function TrapBuilder() {
  const [presets, setPresets] = useState<TrapPreset[]>([]);
  const [mode, setMode] = useState<"preset" | "u-channel">("preset");
  const [selectedId, setSelectedId] = useState("a");
  const [uChannel, setUChannel] = useState<UChannelParameters>(DEFAULT_U_CHANNEL);
  const [electrodes, setElectrodes] = useState<Electrode[]>([]);
  const [solver, setSolver] = useState<"fd" | "bem">("fd");
  const [slider, setSlider] = useState(0);
  const [gridSize, setGridSize] = useState(121);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [sweepPoints, setSweepPoints] = useState<{ parameter_value: number; trap_depth_micro_ev: number }[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getTraps()
      .then((loaded) => {
        setPresets(loaded);
        setElectrodes(loaded[0]?.electrodes ?? []);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load traps"));
  }, []);

  const selected = useMemo(() => presets.find((preset) => preset.id === selectedId), [presets, selectedId]);

  function choosePreset(id: string) {
    const preset = presets.find((item) => item.id === id);
    setSelectedId(id);
    setElectrodes(preset?.electrodes ?? []);
    setResult(null);
  }

  function updateElectrode(index: number, patch: Partial<Electrode>) {
    setElectrodes((current) => current.map((electrode, i) => (i === index ? { ...electrode, ...patch } : electrode)));
  }

  async function runSimulation() {
    setBusy(true);
    setError(null);
    try {
      const response = await simulateTrap({
        ...(mode === "u-channel" ? { u_channel: uChannel } : { preset_id: selectedId, electrodes }),
        solver,
        hyperbolic_slider: slider,
        grid_size: gridSize
      });
      setResult(response);
      setElectrodes(response.electrodes);
      if (mode === "u-channel") {
        const values = [-40, -20, 0, 20, 40].map((delta) => clamp(uChannel.opening_width + delta, 40, 420));
        const sweep = await sweepUChannel({ base: uChannel, parameter: "opening_width", values, grid_size: 61 });
        setSweepPoints(sweep.points.map((point) => ({ parameter_value: point.parameter_value, trap_depth_micro_ev: point.trap_depth_micro_ev })));
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">Ion trap · finite difference / BEM</p>
          <h1>RF potential and pseudopotential (cross-section)</h1>
          <p>
            Set parameters at right and run simulation. Figures use a matplotlib-like layout: RdBu diverging colors for φ<sub>RF</sub>, viridis-like sequential colors for pseudopotential (µeV), black electrode outlines, and a red crosshair at the origin.
          </p>
        </div>
        <button onClick={runSimulation} disabled={busy || electrodes.length === 0}>
          {busy ? "Solving…" : "Run simulation"}
        </button>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="workspace">
        <section className="panel result">
          <div className="result-header">
            <h2>Plots</h2>
            <div className="depth-card">
              <span>Trap depth</span>
              <strong>{result ? `${result.trap_depth_micro_ev.toLocaleString(undefined, { maximumFractionDigits: 2 })} µeV` : "Run simulation"}</strong>
            </div>
          </div>
          <p className="plot-caption">
            Pseudopotential panel windows ±{PSEUDO_PANEL_HALF_WIDTH_UM}&nbsp;µm about the origin; dashed green ellipse is a 90&nbsp;µm-radius guide at (0,&nbsp;0).
          </p>
          <TrapPlots electrodes={electrodes} result={result} presetLabel={mode === "u-channel" ? "U-channel blade trap" : selected?.name ?? ""} showBowl />
          <div className="status-grid">
            <div>
              <span>RF null (µm)</span>
              <strong>{result ? `(${result.rf_null_um[0].toFixed(2)}, ${result.rf_null_um[1].toFixed(2)})` : "—"}</strong>
            </div>
            <div>
              <span>Laplace bulk</span>
              <strong className={result?.validation.laplace_bulk_passed ? "pass" : "warn"}>{result ? (result.validation.laplace_bulk_passed ? "PASS" : "FAIL") : "—"}</strong>
            </div>
            <div>
              <span>Electrode ΔV</span>
              <strong className={result?.validation.electrode_voltage_passed ? "pass" : "warn"}>{result ? (result.validation.electrode_voltage_passed ? "PASS" : "FAIL") : "—"}</strong>
            </div>
          </div>
          {result && (
            <div className="metrics-grid">
              <div>
                <span>Secular f₁</span>
                <strong>{result.metrics.secular ? `${(result.metrics.secular.frequency_hz[0] / 1e6).toFixed(3)} MHz` : "—"}</strong>
              </div>
              <div>
                <span>Secular f₂</span>
                <strong>{result.metrics.secular ? `${(result.metrics.secular.frequency_hz[1] / 1e6).toFixed(3)} MHz` : "—"}</strong>
              </div>
              <div>
                <span>Harmonicity q₄/q₂</span>
                <strong>{result.metrics.harmonicity ? result.metrics.harmonicity.quartic_to_quadratic.toExponential(2) : "—"}</strong>
              </div>
              <div>
                <span>Fit radius</span>
                <strong>{result.metrics.harmonicity ? `${result.metrics.harmonicity.fit_radius_um.toFixed(0)} µm` : "—"}</strong>
              </div>
            </div>
          )}
          {result && (
            <div className="multipole-grid">
              {Object.entries(result.multipole_ratios).map(([name, value]) => (
                <div key={name}>
                  <span>{name}</span>
                  <strong>{value.toExponential(2)}</strong>
                </div>
              ))}
            </div>
          )}
          {result?.warnings.map((warning) => (
            <p className="warning" key={warning}>
              {warning}
            </p>
          ))}
          <SweepTrend points={sweepPoints} />
          <p className="hint-footer">NEXT_PUBLIC_ION_TRAP_API_URL must point at your deployed FastAPI host (localhost only works here on your machine).</p>
        </section>

        <aside className="panel builder">
          <h2>Geometry & solver</h2>
          <label>
            Geometry mode
            <select value={mode} onChange={(event) => {
              setMode(event.target.value as "preset" | "u-channel");
              setResult(null);
              setSweepPoints([]);
            }}>
              <option value="preset">Reference presets</option>
              <option value="u-channel">U-channel blade trap</option>
            </select>
          </label>
          {mode === "preset" ? (
          <label>
            Stored trap preset
            <select value={selectedId} onChange={(event) => choosePreset(event.target.value)}>
              {presets.map((preset) => (
                <option key={preset.id} value={preset.id}>
                  {preset.name}
                </option>
              ))}
            </select>
          </label>
          ) : null}
          {mode === "preset" && selected ? <p className="description">{selected.description}</p> : null}
          {mode === "u-channel" ? (
            <>
              <p className="description">Parametric U-channel opening upward. Drag handles or edit values below.</p>
              <UChannelPreview params={uChannel} onChange={(patch) => setUChannel((current) => ({ ...current, ...patch }))} />
              <label>
                Open / close U-channel: {uChannel.opening_width.toFixed(0)} µm
                <input type="range" min={40} max={420} step={5} value={uChannel.opening_width} onChange={(event) => setUChannel((current) => ({ ...current, opening_width: Number(event.target.value) }))} />
              </label>
              <div className="control-row three">
                <label>Blade h<input type="number" value={uChannel.blade_height} onChange={(event) => setUChannel((c) => ({ ...c, blade_height: Number(event.target.value) }))} /></label>
                <label>Thick<input type="number" value={uChannel.blade_thickness} onChange={(event) => setUChannel((c) => ({ ...c, blade_thickness: Number(event.target.value) }))} /></label>
                <label>Gap<input type="number" value={uChannel.gap_to_ion} onChange={(event) => setUChannel((c) => ({ ...c, gap_to_ion: Number(event.target.value) }))} /></label>
                <label>Curve<input type="number" step={0.05} value={uChannel.bezier_curvature} onChange={(event) => setUChannel((c) => ({ ...c, bezier_curvature: Number(event.target.value) }))} /></label>
                <label>Angle<input type="number" value={uChannel.blade_angle_deg} onChange={(event) => setUChannel((c) => ({ ...c, blade_angle_deg: Number(event.target.value) }))} /></label>
                <label>RF basis<input type="number" step={0.1} value={uChannel.rf_voltage} onChange={(event) => setUChannel((c) => ({ ...c, rf_voltage: Number(event.target.value) }))} /></label>
              </div>
            </>
          ) : null}

          <div className="control-row">
            <label>
              Solver
              <select value={solver} onChange={(event) => setSolver(event.target.value as "fd" | "bem")}>
                <option value="fd">Finite difference</option>
                <option value="bem">BEM reference</option>
              </select>
            </label>
            <label>
              Grid
              <input type="number" min={41} max={401} step={20} value={gridSize} onChange={(event) => setGridSize(Number(event.target.value))} />
            </label>
          </div>

          {mode === "preset" ? <label>
            Hyperbolic shape · {slider.toFixed(2)}
            <input type="range" min={0} max={1} step={0.05} value={slider} onChange={(event) => setSlider(Number(event.target.value))} />
          </label> : null}

          {mode === "preset" ? <div className="electrode-list">
            {electrodes.map((electrode, index) => (
              <div className="electrode-card" key={electrode.id}>
                <strong>{electrode.label}</strong>
                <div className="grid-inputs">
                  <label>
                    x
                    <input type="number" value={electrode.cx} onChange={(event) => updateElectrode(index, { cx: Number(event.target.value) })} />
                  </label>
                  <label>
                    y
                    <input type="number" value={electrode.cy} onChange={(event) => updateElectrode(index, { cy: Number(event.target.value) })} />
                  </label>
                  <label>
                    w
                    <input type="number" value={electrode.width} onChange={(event) => updateElectrode(index, { width: Number(event.target.value) })} />
                  </label>
                  <label>
                    h
                    <input type="number" value={electrode.height} onChange={(event) => updateElectrode(index, { height: Number(event.target.value) })} />
                  </label>
                  <label>
                    V
                    <input type="number" step={0.1} value={electrode.voltage} onChange={(event) => updateElectrode(index, { voltage: Number(event.target.value) })} />
                  </label>
                </div>
              </div>
            ))}
          </div> : null}
        </aside>
      </section>
    </main>
  );
}
