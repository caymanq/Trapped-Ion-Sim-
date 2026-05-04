"use client";

import type { Electrode, SimulationResponse } from "../lib/api";

type Props = {
  electrodes: Electrode[];
  result: SimulationResponse | null;
  width?: number;
  height?: number;
};

function colourFor(electrode: Electrode) {
  if (electrode.voltage > 0) return "#ef4444";
  if (electrode.voltage < 0) return "#3b82f6";
  return "#e5e7eb";
}

export function TrapCanvas({ electrodes, result, width = 720, height = 520 }: Props) {
  const domain = 500;
  const sx = (x: number) => ((x + domain) / (2 * domain)) * width;
  const sy = (y: number) => height - ((y + domain) / (2 * domain)) * height;
  const grid = result?.pseudopotential_micro_ev;
  const maxPseudo = grid ? Math.max(...grid.flat().filter(Number.isFinite), 1) : 1;

  return (
    <svg className="trap-canvas" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Trap geometry and pseudopotential">
      <rect width={width} height={height} fill="#07111f" />
      {grid && grid.length > 0 && (
        <g opacity={0.72}>
          {grid.map((row, iy) =>
            row.map((value, ix) => {
              if (ix % 3 !== 0 || iy % 3 !== 0) return null;
              const t = Math.min(1, Math.max(0, value / maxPseudo));
              const fill = `rgb(${Math.round(40 + 180 * t)}, ${Math.round(80 + 80 * t)}, ${Math.round(180 - 130 * t)})`;
              const cellW = width / row.length;
              const cellH = height / grid.length;
              return <rect key={`${ix}-${iy}`} x={ix * cellW} y={iy * cellH} width={cellW + 1} height={cellH + 1} fill={fill} />;
            })
          )}
        </g>
      )}
      <line x1={sx(-domain)} x2={sx(domain)} y1={sy(0)} y2={sy(0)} stroke="#64748b" strokeDasharray="4 6" />
      <line x1={sx(0)} x2={sx(0)} y1={sy(-domain)} y2={sy(domain)} stroke="#64748b" strokeDasharray="4 6" />
      {electrodes.map((electrode) => {
        const x = sx(electrode.cx - electrode.width / 2);
        const y = sy(electrode.cy + electrode.height / 2);
        const w = (electrode.width / (2 * domain)) * width;
        const h = (electrode.height / (2 * domain)) * height;
        const inset = (electrode.curvature ?? 0) * w * 0.16;
        const d = `M ${x} ${y} Q ${x + inset} ${y + h / 2} ${x} ${y + h} L ${x + w} ${y + h} Q ${x + w - inset} ${y + h / 2} ${x + w} ${y} Z`;
        return (
          <g key={electrode.id}>
            <path d={d} fill={colourFor(electrode)} stroke="#f8fafc" strokeWidth="1.4" opacity="0.9" />
            <text x={x + w / 2} y={y + h / 2 + 4} textAnchor="middle" className="electrode-label">
              {electrode.label}
            </text>
          </g>
        );
      })}
      <circle cx={sx(0)} cy={sy(0)} r="6" fill="#facc15" stroke="#111827" strokeWidth="2" />
    </svg>
  );
}
