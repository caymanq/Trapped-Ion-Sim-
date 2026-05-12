"use client";

import type { Electrode, SimulationResponse } from "../lib/api";

type Props = {
  electrodes: Electrode[];
  result: SimulationResponse | null;
  width?: number;
  height?: number;
};

/** Muted cool palette aligned with electrode legend */
function colourFor(electrode: Electrode) {
  if (electrode.voltage > 0) return "#74606e";
  if (electrode.voltage < 0) return "#5f6f7d";
  return "#6f7780";
}

/** Low-glare pseudopotential scale: deep navy toward grey-blue highs */
function pseudopotFill(t: number) {
  const u = Math.min(1, Math.max(0, t));
  const r = Math.round(12 + u * 45);
  const g = Math.round(18 + u * 55);
  const b = Math.round(32 + u * 68);
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
      <rect width={width} height={height} fill="#080b10" />

      <defs>
        <radialGradient id="field-vignette" cx="50%" cy="45%" r="75%">
          <stop offset="0%" stopColor="rgba(120, 135, 150, 0.04)" />
          <stop offset="100%" stopColor="rgba(0, 0, 0, 0.42)" />
        </radialGradient>
      </defs>
      <rect width={width} height={height} fill="url(#field-vignette)" pointerEvents="none" />

      {grid && grid.length > 0 && (
        <g opacity={0.72}>
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
      <line x1={sx(-domain)} x2={sx(domain)} y1={sy(0)} y2={sy(0)} stroke="rgba(100, 120, 138, 0.32)" strokeWidth="1" strokeDasharray="3 10" />
      <line x1={sx(0)} x2={sx(0)} y1={sy(-domain)} y2={sy(domain)} stroke="rgba(100, 120, 138, 0.32)" strokeWidth="1" strokeDasharray="3 10" />
      <rect x="0" y="0" width={width} height={height} fill="none" stroke="rgba(90, 110, 128, 0.2)" strokeWidth="1" />

      {electrodes.map((electrode) => {
        const x = sx(electrode.cx - electrode.width / 2);
        const y = sy(electrode.cy + electrode.height / 2);
        const w = (electrode.width / (2 * domain)) * width;
        const h = (electrode.height / (2 * domain)) * height;
        /* Match backend geometry.py: widen at mid-height (vertical edges bow toward ion at origin). */
        const inset = (electrode.curvature ?? 0) * w * 0.16;
        const d = `M ${x} ${y} Q ${x - inset} ${y + h / 2} ${x} ${y + h} L ${x + w} ${y + h} Q ${x + w + inset} ${y + h / 2} ${x + w} ${y} Z`;
        return (
          <g key={electrode.id}>
            <path d={d} fill={colourFor(electrode)} fillOpacity={0.9} stroke="rgba(200, 210, 220, 0.35)" strokeWidth="1" opacity={1} />
            <text x={x + w / 2} y={y + h / 2 + 4} textAnchor="middle" className="electrode-label">
              {electrode.label}
            </text>
          </g>
        );
      })}
      <circle cx={sx(0)} cy={sy(0)} r="5.5" fill="#8f866f" stroke="rgba(120, 130, 145, 0.5)" strokeWidth="1.2" />
    </svg>
  );
}
