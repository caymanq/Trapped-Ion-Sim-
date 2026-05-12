"use client";

import { useEffect, useMemo, useState } from "react";
import { getTraps, simulateTrap, type Electrode, type SimulationResponse, type TrapPreset } from "../lib/api";
import { PSEUDO_PANEL_HALF_WIDTH_UM, TrapPlots } from "./TrapPlots";

export function TrapBuilder() {
  const [presets, setPresets] = useState<TrapPreset[]>([]);
  const [selectedId, setSelectedId] = useState("a");
  const [electrodes, setElectrodes] = useState<Electrode[]>([]);
  const [solver, setSolver] = useState<"fd" | "bem">("fd");
  const [slider, setSlider] = useState(0);
  const [gridSize, setGridSize] = useState(121);
  const [result, setResult] = useState<SimulationResponse | null>(null);
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
        preset_id: selectedId,
        electrodes,
        solver,
        hyperbolic_slider: slider,
        grid_size: gridSize
      });
      setResult(response);
      setElectrodes(response.electrodes);
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
          <TrapPlots electrodes={electrodes} result={result} presetLabel={selected?.name ?? ""} />
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
          <p className="hint-footer">NEXT_PUBLIC_ION_TRAP_API_URL must point at your deployed FastAPI host (localhost only works here on your machine).</p>
        </section>

        <aside className="panel builder">
          <h2>Geometry & solver</h2>
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
          {selected && <p className="description">{selected.description}</p>}

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

          <label>
            Hyperbolic shape · {slider.toFixed(2)}
            <input type="range" min={0} max={1} step={0.05} value={slider} onChange={(event) => setSlider(Number(event.target.value))} />
          </label>

          <div className="electrode-list">
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
          </div>
        </aside>
      </section>
    </main>
  );
}
