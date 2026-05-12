"use client";

import type { Electrode, SimulationResponse } from "../lib/api";

type Props = {
  electrodes: Electrode[];
  result: SimulationResponse | null;
  width?: number;
  height?: number;
};

function colourFor(electrode: Electrode) {
  if (electrode.voltage > 0) return "#ff4da6";
  if (electrode.voltage < 0) return "#39f9ff";
  return "#9eb4c8";
}

/** Neon heatmap reminiscent of CRT / raylib demos: dark → cyan → magenta */
function pseudopotFill(t: number) {
  const u = Math.min(1, Math.max(0, t));
  if (u < 0.45) {
    const s = u / 0.45;
    const r = Math.round(10 + s * 20);
    const g = Math.round(15 + s * 90);
    const b = Math.round(28 + s * 120);
    return `rgb(${r}, ${g}, ${b})`;
  }
  if (u < 0.75) {
    const s = (u - 0.45) / 0.3;
    const r = Math.round(30 + s * 120);
    const g = Math.round(105 + s * 100);
    const b = Math.round(148 + s * 60);
    return `rgb(${r}, ${g}, ${b})`;
  }
  const s = (u - 0.75) / 0.25;
  const r = Math.round(150 + s * 105);
  const g = Math.round(205 - s * 120);
  const b = Math.round(208 - s * 40);
  return `rgb(${r}, ${g}, ${b})`;
}

export function TrapCanvas({ electrodes, result, width = 720, height = 520 }: Props) {
  const domain = 500;
  const sx = (x: number) => ((x + domain) / (2 * domain)) * width;
  const sy = (y: number) => height - ((y + domain) / (2 * domain)) * height;
  const grid = result?.pseudopotential_micro_ev;
  const maxPseudo = grid ? Math.max(...grid.flat().filter(Number.isFinite), 1) : 1;

  return (
    <svg className="trap-canvas" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Trap geometry and pseudopotential">
      <rect width={width} height={height} fill="#020207" />

      {/* Subtle CRT-style vignette */}
      <defs>
        <radialGradient id="crt-vignette" cx="50%" cy="45%" r="75%">
          <stop offset="0%" stopColor="rgba(255,255,255,0.03)" />
          <stop offset="100%" stopColor="rgba(0,0,0,0.35)" />
        </radialGradient>
      </defs>
      <rect width={width} height={height} fill="url(#crt-vignette)" pointerEvents="none" />

      {grid && grid.length > 0 && (
        <g opacity={0.78}>
          {grid.map((row, iy) =>
            row.map((value, ix) => {
              if (ix % 3 !== 0 || iy % 3 !== 0) return null;
              const u = Math.min(1, Math.max(0, value / maxPseudo));
              const fill = pseudopotFill(u);
              const cellW = width / row.length;
              const cellH = height / grid.length;
              return <rect key={`${ix}-${iy}`} x={ix * cellW} y={iy * cellH} width={cellW + 1} height={cellH + 1} fill={fill} />;
            })
          )}
        </g>
      )}
      {/* Axes wireframe */}
      <line x1={sx(-domain)} x2={sx(domain)} y1={sy(0)} y2={sy(0)} stroke="rgba(57,249,255,0.35)" strokeWidth="1" strokeDasharray="3 8" />
      <line x1={sx(0)} x2={sx(0)} y1={sy(-domain)} y2={sy(domain)} stroke="rgba(57,249,255,0.35)" strokeWidth="1" strokeDasharray="3 8" />
      <rect x="0" y="0" width={width} height={height} fill="none" stroke="rgba(255,77,166,0.15)" strokeWidth="1" />

      {electrodes.map((electrode) => {
        const x = sx(electrode.cx - electrode.width / 2);
        const y = sy(electrode.cy + electrode.height / 2);
        const w = (electrode.width / (2 * domain)) * width;
        const h = (electrode.height / (2 * domain)) * height;
        const inset = (electrode.curvature ?? 0) * w * 0.16;
        const d = `M ${x} ${y} Q ${x + inset} ${y + h / 2} ${x} ${y + h} L ${x + w} ${y + h} Q ${x + w - inset} ${y + h / 2} ${x + w} ${y} Z`;
        return (
          <g key={electrode.id}>
            <path d={d} fill={colourFor(electrode)} fillOpacity={0.88} stroke="#f0faff" strokeWidth="1.1" opacity={0.95} />
            <text x={x + w / 2} y={y + h / 2 + 4} textAnchor="middle" className="electrode-label">
              {electrode.label}
            </text>
          </g>
        );
      })}
      <circle cx={sx(0)} cy={sy(0)} r="6" fill="#ff9f1c" stroke="#39f9ff" strokeWidth="1.5" />
    </svg>
  );
}
