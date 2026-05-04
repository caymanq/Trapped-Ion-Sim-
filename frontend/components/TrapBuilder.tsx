"use client";

import { useEffect, useMemo, useState } from "react";
import { getTraps, simulateTrap, type Electrode, type SimulationResponse, type TrapPreset } from "../lib/api";
import { TrapCanvas } from "./TrapCanvas";

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
          <p className="eyebrow">Ion Trap Designer</p>
          <h1>Build trap geometries and inspect pseudopotentials.</h1>
          <p>
            The Vercel frontend edits electrode geometry while the Python compute API returns the RF solution,
            pseudopotential, trap depth, and physics validation.
          </p>
        </div>
        <button onClick={runSimulation} disabled={busy || electrodes.length === 0}>
          {busy ? "Solving..." : "Run Simulation"}
        </button>
      </header>

      {error && <div className="error">{error}</div>}

      <section className="workspace">
        <aside className="panel builder">
          <h2>Trap Geometry Builder</h2>
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
                <option value="bem">BEM reference mode</option>
              </select>
            </label>
            <label>
              Grid
              <input type="number" min={41} max={401} step={20} value={gridSize} onChange={(event) => setGridSize(Number(event.target.value))} />
            </label>
          </div>

          <label>
            Hyperbolic electrode shape: {slider.toFixed(2)}
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

        <section className="panel result">
          <div className="result-header">
            <h2>Pseudopotential View</h2>
            <div className="depth-card">
              <span>Trap depth</span>
              <strong>{result ? `${result.trap_depth_micro_ev.toLocaleString(undefined, { maximumFractionDigits: 2 })} micro eV` : "Run simulation"}</strong>
            </div>
          </div>
          <TrapCanvas electrodes={electrodes} result={result} />
          <div className="status-grid">
            <div>
              <span>RF null</span>
              <strong>{result ? `(${result.rf_null_um[0].toFixed(2)}, ${result.rf_null_um[1].toFixed(2)}) um` : "Ion at origin"}</strong>
            </div>
            <div>
              <span>Laplace bulk</span>
              <strong className={result?.validation.laplace_bulk_passed ? "pass" : "warn"}>{result ? (result.validation.laplace_bulk_passed ? "PASS" : "FAIL") : "Pending"}</strong>
            </div>
            <div>
              <span>Electrode voltage</span>
              <strong className={result?.validation.electrode_voltage_passed ? "pass" : "warn"}>{result ? (result.validation.electrode_voltage_passed ? "PASS" : "FAIL") : "Pending"}</strong>
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
        </section>
      </section>
    </main>
  );
}
