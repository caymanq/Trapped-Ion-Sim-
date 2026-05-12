"use client";

import { useId, useMemo } from "react";
import type { Electrode, SimulationResponse } from "../lib/api";

type WorldBox = { left: number; top: number; width: number; height: number };

/** Affine map (µm, trap y-up) → SVG pixels (y-down). */
function makeProjector(xMin: number, xMax: number, yMin: number, yMax: number, box: WorldBox) {
  const sx = (x: number) => box.left + ((x - xMin) / (xMax - xMin)) * box.width;
  const sy = (y: number) => box.top + box.height - ((y - yMin) / (yMax - yMin)) * box.height;
  return { sx, sy };
}

/** Matplotlib RdBu-style: u ∈ [-1, 1] → RGB. */
function rdbu(u: number) {
  const t = Math.max(-1, Math.min(1, u));
  const bl = [33, 102, 172];
  const wh = [247, 247, 247];
  const rd = [178, 24, 43];
  let a: number[];
  let b: number[];
  let s: number;
  if (t <= 0) {
    s = t + 1;
    a = bl;
    b = wh;
  } else {
    s = t;
    a = wh;
    b = rd;
  }
  const r = Math.round(a[0] + (b[0] - a[0]) * s);
  const g = Math.round(a[1] + (b[1] - a[1]) * s);
  const bch = Math.round(a[2] + (b[2] - a[2]) * s);
  return `rgb(${r},${g},${bch})`;
}

/** Compact viridis-like scale (u ∈ [0,1]). */
function viridis(u: number) {
  const t = Math.max(0, Math.min(1, u));
  const stops = [
    [68, 1, 84],
    [65, 68, 135],
    [42, 120, 142],
    [34, 168, 132],
    [122, 209, 81],
    [253, 231, 37]
  ];
  const n = stops.length - 1;
  const f = t * n;
  const i = Math.min(n - 1, Math.floor(f));
  const w = f - i;
  const a = stops[i];
  const b = stops[i + 1];
  const r = Math.round(a[0] + (b[0] - a[0]) * w);
  const g = Math.round(a[1] + (b[1] - a[1]) * w);
  const bc = Math.round(a[2] + (b[2] - a[2]) * w);
  return `rgb(${r},${g},${bc})`;
}

function findSubRange(values: number[], lo: number, hi: number): [number, number] | null {
  let i0 = -1;
  let i1 = -1;
  for (let i = 0; i < values.length; i++) {
    if (values[i] >= lo && values[i] <= hi) {
      if (i0 < 0) i0 = i;
      i1 = i;
    }
  }
  if (i0 < 0) return null;
  return [i0, i1];
}

function fmtTick(n: number) {
  if (!Number.isFinite(n)) return "—";
  const a = Math.abs(n);
  if (a >= 1e4 || (a < 1e-2 && a > 0)) return n.toExponential(1);
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function electrodeOutlineD(e: Electrode, sx: (x: number) => number, sy: (y: number) => number) {
  if (e.outline && e.outline.length >= 3) {
    return e.outline
      .map(([x, y], index) => `${index === 0 ? "M" : "L"} ${sx(x).toFixed(2)},${sy(y).toFixed(2)}`)
      .join(" ")
      .concat(" Z");
  }
  const xL = e.cx - e.width / 2;
  const xR = e.cx + e.width / 2;
  const yT = e.cy + e.height / 2;
  const yB = e.cy - e.height / 2;
  const bulge = (e.curvature ?? 0) * e.width * 0.16;
  const p = (x: number, y: number) => `${sx(x).toFixed(2)},${sy(y).toFixed(2)}`;
  return `M ${p(xL, yT)} Q ${p(xL - bulge, e.cy)} ${p(xL, yB)} L ${p(xR, yB)} Q ${p(xR + bulge, e.cy)} ${p(xR, yT)} Z`;
}

type PlotCell = { key: string; x: number; y: number; w: number; h: number; fill: string };

type HeatmapFigureProps = {
  title: string;
  xLabel: string;
  yLabel: string;
  colorbarLabel: string;
  cmap: "rdbu" | "viridis";
  xs: number[];
  ys: number[];
  grid: number[][];
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
  electrodes: Electrode[];
  crosshairWorld: [number, number];
  circleWorld?: { cx: number; cy: number; r: number };
  formatColorTick: (v: number) => string;
};

function HeatmapFigure({
  title,
  xLabel,
  yLabel,
  colorbarLabel,
  cmap,
  xs,
  ys,
  grid,
  xMin,
  xMax,
  yMin,
  yMax,
  electrodes,
  crosshairWorld,
  circleWorld,
  formatColorTick
}: HeatmapFigureProps) {
  const uid = useId().replace(/:/g, "");
  const marginL = 46;
  const marginR = 12;
  const marginT = 36;
  const marginB = 44;
  const cbW = 14;
  const cbGap = 10;
  const plotW = 320;
  const plotH = 300;
  const innerW = plotW - marginL - marginR - cbW - cbGap;
  const innerH = plotH - marginT - marginB;
  const box: WorldBox = { left: marginL, top: marginT, width: innerW, height: innerH };
  const { sx, sy } = makeProjector(xMin, xMax, yMin, yMax, box);
  const clipId = `fx-${uid}`;

  const { cells, vmin, vmax } = useMemo(() => {
    const ny = grid.length;
    const nx = ny > 0 ? grid[0].length : 0;
    if (!nx || !ny) {
      return { cells: [] as PlotCell[], vmin: 0, vmax: 1 };
    }
    const flat = grid.flat().filter(Number.isFinite);
    let vmin_: number;
    let vmax_: number;
    let norm: (v: number) => number;
    if (cmap === "rdbu") {
      const absMax = Math.max(...flat.map((z) => Math.abs(z)), 1e-9);
      vmin_ = -absMax;
      vmax_ = absMax;
      norm = (v) => (Number.isFinite(v) ? Math.max(-1, Math.min(1, v / absMax)) : 0);
    } else {
      vmin_ = Math.min(...flat);
      vmax_ = Math.max(...flat);
      const span = Math.max(vmax_ - vmin_, 1e-12);
      norm = (v) => (Number.isFinite(v) ? Math.max(0, Math.min(1, (v - vmin_) / span)) : 0);
    }
    const sx_ = (x: number) => box.left + ((x - xMin) / (xMax - xMin)) * box.width;
    const sy_ = (y: number) => box.top + box.height - ((y - yMin) / (yMax - yMin)) * box.height;
    const stride = Math.max(1, Math.floor(nx / 140));
    const dx = xs.length > 1 ? xs[1] - xs[0] : 1;
    const dy = ys.length > 1 ? ys[1] - ys[0] : 1;
    const cells_: PlotCell[] = [];
    for (let iy = 0; iy < ny; iy += stride) {
      const y0 = ys[iy];
      const y1 = iy + stride < ny ? ys[iy + stride] : y0 + dy * stride;
      const yTop = Math.max(y0, y1);
      const yBot = Math.min(y0, y1);
      for (let ix = 0; ix < nx; ix += stride) {
        const x0 = xs[ix];
        const x1 = ix + stride < nx ? xs[ix + stride] : x0 + dx * stride;
        const xl = Math.min(x0, x1);
        const xr = Math.max(x0, x1);
        const row = grid[iy];
        const v = row ? row[ix] ?? 0 : 0;
        const t = norm(v);
        const fill = cmap === "rdbu" ? rdbu(t) : viridis(t);
        const px0 = sx_(xl);
        const px1 = sx_(xr);
        const pyT = sy_(yTop);
        const pyB = sy_(yBot);
        cells_.push({
          key: `${ix}-${iy}`,
          x: px0,
          y: pyT,
          w: Math.max(px1 - px0, 0.5),
          h: Math.max(pyB - pyT, 0.5),
          fill
        });
      }
    }
    return { cells: cells_, vmin: vmin_, vmax: vmax_ };
  }, [grid, xs, ys, cmap, xMin, xMax, yMin, yMax, box.left, box.top, box.width, box.height]);

  const ticks = [xMin, (xMin + xMax) / 2, xMax];
  const yTicks = [yMin, (yMin + yMax) / 2, yMax];
  const cx = sx(crosshairWorld[0]);
  const cy = sy(crosshairWorld[1]);
  const circleRx =
    circleWorld != null ? (Math.abs(circleWorld.r) / (xMax - xMin)) * box.width : 0;
  const circleRy =
    circleWorld != null ? (Math.abs(circleWorld.r) / (yMax - yMin)) * box.height : 0;
  const gradId = `cb-${uid}-${cmap}`;

  const cbLeft = marginL + innerW + cbGap;
  const cbTop = marginT;

  return (
    <div className="figure-wrap">
      <div className="figure-title">{title}</div>
      <svg className="figure-svg" viewBox={`0 0 ${plotW} ${plotH}`} role="img" aria-label={title}>
        <rect x="0" y="0" width={plotW} height={plotH} fill="#ffffff" />
        <defs>
          <clipPath id={clipId}>
            <rect x={box.left} y={box.top} width={box.width} height={box.height} />
          </clipPath>
          <linearGradient id={gradId} x1="0%" y1="100%" x2="0%" y2="0%">
            {Array.from({ length: 33 }, (_, i) => {
              const u = i / 32;
              const stopColor = cmap === "rdbu" ? rdbu(-1 + 2 * u) : viridis(u);
              const offsetPct = `${(u * 100).toFixed(2)}%`;
              return <stop key={i} offset={offsetPct} stopColor={stopColor} />;
            })}
          </linearGradient>
        </defs>
        <rect x={box.left} y={box.top} width={box.width} height={box.height} fill="#fafafa" stroke="#333" strokeWidth="0.75" />

        <g clipPath={`url(#${clipId})`}>
          {cells.map((c) => (
            <rect key={c.key} x={c.x} y={c.y} width={c.w} height={c.h} fill={c.fill} stroke="none" />
          ))}
          {electrodes.map((e) => (
            <path key={e.id} d={electrodeOutlineD(e, sx, sy)} fill="none" stroke="#111" strokeWidth="0.9" vectorEffect="non-scaling-stroke" />
          ))}
          {circleWorld ? (
            <ellipse
              cx={sx(circleWorld.cx)}
              cy={sy(circleWorld.cy)}
              rx={circleRx}
              ry={circleRy}
              fill="none"
              stroke="#2ca02d"
              strokeWidth="1"
              strokeDasharray="4 3"
              vectorEffect="non-scaling-stroke"
            />
          ) : null}
          <line x1={cx} x2={cx} y1={box.top} y2={box.top + box.height} stroke="#d62728" strokeWidth="0.9" vectorEffect="non-scaling-stroke" />
          <line x1={box.left} x2={box.left + box.width} y1={cy} y2={cy} stroke="#d62728" strokeWidth="0.9" vectorEffect="non-scaling-stroke" />
        </g>

        {ticks.map((t) => {
          const x = sx(t);
          return (
            <g key={`xt-${t}`}>
              <line x1={x} x2={x} y1={box.top + box.height} y2={box.top + box.height + 4} stroke="#333" strokeWidth="0.6" />
              <text className="figure-tick" x={x} y={plotH - 10} textAnchor="middle">
                {fmtTick(t)}
              </text>
            </g>
          );
        })}
        {yTicks.map((t) => {
          const y = sy(t);
          return (
            <g key={`yt-${t}`}>
              <line x1={box.left - 4} x2={box.left} y1={y} y2={y} stroke="#333" strokeWidth="0.6" />
              <text className="figure-tick" x={marginL - 8} y={y + 3} textAnchor="end">
                {fmtTick(t)}
              </text>
            </g>
          );
        })}

        <text className="figure-axis-label" x={box.left + box.width / 2} y={plotH - 2} textAnchor="middle">
          {xLabel}
        </text>
        <text className="figure-axis-label" x={14} y={box.top + box.height / 2} textAnchor="middle" transform={`rotate(-90, 14, ${box.top + box.height / 2})`}>
          {yLabel}
        </text>

        <rect x={cbLeft} y={cbTop} width={cbW} height={innerH} fill={`url(#${gradId})`} stroke="#333" strokeWidth="0.6" />
        <text className="figure-colorbar-val" x={cbLeft + cbW + 3} y={cbTop + 5} dominantBaseline="hanging">
          {formatColorTick(vmax)}
        </text>
        <text className="figure-colorbar-val" x={cbLeft + cbW + 3} y={cbTop + innerH}>
          {formatColorTick(vmin)}
        </text>
        <text className="figure-colorbar-label" x={cbLeft + cbW / 2} y={cbTop + innerH + 26} textAnchor="middle">
          {colorbarLabel}
        </text>
      </svg>
    </div>
  );
}

type Props = {
  electrodes: Electrode[];
  result: SimulationResponse | null;
  presetLabel?: string;
  showBowl?: boolean;
};

/** Pseudopotential panel half-extent ± this value (µm) around (0,0). */
export const PSEUDO_PANEL_HALF_WIDTH_UM = 250;

function BowlFigure({ result }: { result: SimulationResponse }) {
  const xs = result.x_um;
  const ys = result.y_um;
  const grid = result.pseudopotential_micro_ev;
  const extent = 120;
  const xr = findSubRange(xs, -extent, extent);
  const yr = findSubRange(ys, -extent, extent);
  if (!xr || !yr) return null;
  const [x0, x1] = xr;
  const [y0, y1] = yr;
  const crop = grid.slice(y0, y1 + 1).map((row) => row.slice(x0, x1 + 1));
  const flat = crop.flat().filter(Number.isFinite);
  const min = Math.min(...flat);
  const max = Math.max(...flat);
  const span = Math.max(max - min, 1e-12);
  const width = 360;
  const height = 210;
  const cells = crop.flatMap((row, iy) =>
    row.map((value, ix) => {
      const x = (ix / Math.max(row.length - 1, 1)) * width;
      const y = (iy / Math.max(crop.length - 1, 1)) * height;
      const lift = ((value - min) / span) * 70;
      return { x, y: y - lift, value };
    })
  );
  return (
    <div className="bowl-wrap">
      <div className="figure-title">local pseudopotential bowl</div>
      <svg className="bowl-svg" viewBox={`0 -80 ${width} ${height + 90}`} role="img" aria-label="Local pseudopotential bowl">
        <rect x="0" y="-80" width={width} height={height + 90} fill="#fff" />
        {cells.map((cell, i) => (
          <circle key={i} cx={cell.x} cy={cell.y} r="1.8" fill={viridis((cell.value - min) / span)} opacity="0.78" />
        ))}
        <line x1="0" x2={width} y1={height} y2={height} stroke="#555" strokeWidth="0.8" />
        <text x={width / 2} y={height + 16} textAnchor="middle" className="figure-axis-label">
          smoothed local view ±{extent} µm (visual only)
        </text>
      </svg>
    </div>
  );
}

export function TrapPlots({ electrodes, result, presetLabel, showBowl = false }: Props) {
  const label = presetLabel?.trim() || "Trap";

  if (!result?.x_um?.length || !result.potential.length) {
    return (
      <div className="plots-placeholder">
        <p className="plots-placeholder-text">Run a simulation to plot φ<sub>RF</sub> and pseudopotential (matplotlib-style).</p>
      </div>
    );
  }

  const { x_um: xs, y_um: ys, potential, pseudopotential_micro_ev: pseudo } = result;
  const xMinFull = xs[0];
  const xMaxFull = xs[xs.length - 1];
  const yMinFull = ys[0];
  const yMaxFull = ys[ys.length - 1];

  const zr = findSubRange(xs, -PSEUDO_PANEL_HALF_WIDTH_UM, PSEUDO_PANEL_HALF_WIDTH_UM);
  const rr = findSubRange(ys, -PSEUDO_PANEL_HALF_WIDTH_UM, PSEUDO_PANEL_HALF_WIDTH_UM);
  let xsZ = xs;
  let ysZ = ys;
  let gridZ = pseudo;
  if (zr && rr) {
    const [jx0, jx1] = zr;
    const [jy0, jy1] = rr;
    xsZ = xs.slice(jx0, jx1 + 1);
    ysZ = ys.slice(jy0, jy1 + 1);
    gridZ = pseudo.slice(jy0, jy1 + 1).map((row) => row.slice(jx0, jx1 + 1));
  }

  const xMinZ = xsZ[0];
  const xMaxZ = xsZ[xsZ.length - 1];
  const yMinZ = ysZ[0];
  const yMaxZ = ysZ[ysZ.length - 1];

  const ch: [number, number] = [0, 0];

  return (
    <>
      <div className="plots-row">
      <HeatmapFigure
        title={`${label} — φ_RF`}
        xLabel="x (µm)"
        yLabel="y (µm)"
        colorbarLabel="φ_RF (V)"
        cmap="rdbu"
        xs={xs}
        ys={ys}
        grid={potential}
        xMin={xMinFull}
        xMax={xMaxFull}
        yMin={yMinFull}
        yMax={yMaxFull}
        electrodes={electrodes}
        crosshairWorld={ch}
        formatColorTick={(v) => v.toFixed(2)}
      />
      <HeatmapFigure
        title={`${label} — pseudopotential`}
        xLabel="x (µm)"
        yLabel="y (µm)"
        colorbarLabel="φ_ps (µeV)"
        cmap="viridis"
        xs={xsZ}
        ys={ysZ}
        grid={gridZ}
        xMin={xMinZ}
        xMax={xMaxZ}
        yMin={yMinZ}
        yMax={yMaxZ}
        electrodes={electrodes}
        crosshairWorld={ch}
        circleWorld={{ cx: 0, cy: 0, r: 90 }}
        formatColorTick={(v) => fmtTick(v)}
      />
      </div>
      {showBowl && result ? <BowlFigure result={result} /> : null}
    </>
  );
}
