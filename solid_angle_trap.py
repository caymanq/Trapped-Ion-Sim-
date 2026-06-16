"""
Gridless 3D half-space RF potential via polygon solid angles, pseudopotential,
and multipole anharmonicity metrics for sketch surface-trap geometries.

Coordinate convention (sketch -> 3D):
  Electrode polygon vertex (x_um, y_um) -> (x_m, y_m, 0) on the chip plane z=0.
  Field points for the ion region -> (x_m, y_m, z_ion_m) with z_ion_m > 0.
"""

from __future__ import annotations

import os
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator

# Lab defaults (match multipole_table_replication.ipynb)
ION_MASS = 9.0121831 * 1.66054e-27  # kg (9Be+)
Q_E = 1.602176634e-19  # C
V_RF_AMP = 200.0  # V peak
OMEGA_RF = 2.0 * np.pi * 40e6  # rad/s

SKETCH_TRAP_ANGLES = (0.0, 22.5, 45.0, 67.5, 90.0)
UM = 1e-6


def _as_3d(point: Sequence[float]) -> np.ndarray:
    p = np.asarray(point, dtype=float).reshape(3)
    return p


def polygon_solid_angle(vertices_3d: np.ndarray, field_point_3d: Sequence[float]) -> float:
    """
    Solid angle (steradians) subtended by a planar polygon from field_point.

    Uses the van Oosterom-Strackee edge sum on unit vectors from the field
    point to each vertex. Vertices should lie in a common plane (typically z=0).
    """
    verts = np.asarray(vertices_3d, dtype=float)
    if verts.ndim != 2 or verts.shape[1] != 3:
        raise ValueError("vertices_3d must be an Nx3 array")
    if len(verts) < 3:
        return 0.0

    p = _as_3d(field_point_3d)
    if abs(p[2]) < 1e-15:
        raise ValueError("field point must not lie in the electrode plane (z > 0 required)")

    vecs = verts - p
    norms = np.linalg.norm(vecs, axis=1)
    if np.any(norms < 1e-18):
        raise ValueError("field point coincides with a polygon vertex")
    e = vecs / norms[:, np.newaxis]

    omega = 0.0
    n = len(e)
    for i in range(n):
        e1 = e[i]
        e2 = e[(i + 1) % n]
        cross = np.cross(e1, e2)
        dot = np.clip(np.dot(e1, e2), -1.0, 1.0)
        omega += np.arctan2(np.linalg.norm(cross), dot)

    return float(omega)


def sketch_poly_to_3d_vertices(poly: Sequence[Sequence[float]]) -> np.ndarray:
    """Map sketch (x_um, y_um) vertices to 3D points on z=0 in meters."""
    pts = np.asarray(poly, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError("polygon must be Nx2 in micrometers")
    return np.column_stack([pts[:, 0] * UM, pts[:, 1] * UM, np.zeros(len(pts))])


def electrode_potential(
    electrode: dict,
    field_point_3d: Sequence[float],
) -> float:
    """Potential at field_point from one electrode held at voltage V (volts)."""
    v = float(electrode.get("V", 0.0))
    if abs(v) < 1e-15:
        return 0.0
    poly = electrode.get("poly")
    if not poly or len(poly) < 3:
        return 0.0
    verts = sketch_poly_to_3d_vertices(poly)
    omega = polygon_solid_angle(verts, field_point_3d)
    return (v / (2.0 * np.pi)) * omega


def trap_phi_rf(
    electrodes: Sequence[dict],
    field_point_3d: Sequence[float],
) -> float:
    """Total normalized RF potential (sum of electrode contributions)."""
    return sum(electrode_potential(e, field_point_3d) for e in electrodes)


def field_point_3d(x_um: float, y_um: float, z_ion_um: float) -> np.ndarray:
    return np.array([x_um * UM, y_um * UM, z_ion_um * UM], dtype=float)


def phi_rf_grid(
    x_1d_um: np.ndarray,
    y_1d_um: np.ndarray,
    z_ion_um: float,
    electrodes: Sequence[dict],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate phi_rf on a 2D chip-plane grid at height z_ion_um."""
    xg, yg = np.meshgrid(x_1d_um, y_1d_um, indexing="xy")
    z_m = z_ion_um * UM
    phi = np.zeros_like(xg, dtype=float)
    for j in range(phi.shape[0]):
        for i in range(phi.shape[1]):
            fp = np.array([xg[j, i] * UM, yg[j, i] * UM, z_m])
            phi[j, i] = trap_phi_rf(electrodes, fp)
    return xg, yg, phi


def phi_rf_grid_vectorized(
    x_1d_um: np.ndarray,
    y_1d_um: np.ndarray,
    z_ion_um: float,
    electrodes: Sequence[dict],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vectorized grid evaluation (loops over electrodes only)."""
    xg, yg = np.meshgrid(x_1d_um, y_1d_um, indexing="xy")
    z_m = z_ion_um * UM
    phi = np.zeros_like(xg, dtype=float)
    for electrode in electrodes:
        v = float(electrode.get("V", 0.0))
        if abs(v) < 1e-15:
            continue
        poly = electrode.get("poly")
        if not poly or len(poly) < 3:
            continue
        verts = sketch_poly_to_3d_vertices(poly)
        for j in range(phi.shape[0]):
            for i in range(phi.shape[1]):
                fp = np.array([xg[j, i] * UM, yg[j, i] * UM, z_m])
                phi[j, i] += (v / (2.0 * np.pi)) * polygon_solid_angle(verts, fp)
    return xg, yg, phi


def pseudopotential_from_phi_rf(
    phi_rf: np.ndarray,
    x_1d_um: np.ndarray,
    y_1d_um: np.ndarray,
    vamp: float = V_RF_AMP,
    omega: float = OMEGA_RF,
    mass: float = ION_MASS,
    charge: float = Q_E,
) -> np.ndarray:
    """
    Phi_ps = q / (4 m Omega^2) * (V_rf |grad phi_rf|)^2  on the x-y grid at fixed z.
    """
    dx_m = (x_1d_um[1] - x_1d_um[0]) * UM
    dy_m = (y_1d_um[1] - y_1d_um[0]) * UM
    gY, gX = np.gradient(phi_rf, dy_m, dx_m)
    grad2 = vamp**2 * (gX**2 + gY**2)
    return charge / (4.0 * mass * omega**2) * grad2


def _point_segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    abx, aby = bx - ax, by - ay
    denom = abx * abx + aby * aby
    if denom <= 1e-30:
        return float(np.hypot(px - ax, py - ay))
    t = np.clip(((px - ax) * abx + (py - ay) * aby) / denom, 0.0, 1.0)
    qx, qy = ax + t * abx, ay + t * aby
    return float(np.hypot(px - qx, py - qy))


def ion_electrode_dist(elecs: Sequence[dict], x0: float, y0: float) -> float:
    """Min distance (um) from (x0,y0) to nearest electrode surface."""
    d = np.inf
    for e in elecs:
        poly = e.get("poly")
        if poly is not None and len(poly) >= 3:
            for i, (ax, ay) in enumerate(poly):
                bx, by = poly[(i + 1) % len(poly)]
                d = min(d, _point_segment_distance(x0, y0, ax, ay, bx, by))
            continue
        cx, cy, w, h = e["cx"], e["cy"], e["w"], e["h"]
        px = np.clip(x0, cx - w / 2, cx + w / 2)
        py = np.clip(y0, cy - h / 2, cy + h / 2)
        d = min(d, np.hypot(px - x0, py - y0))
    return float(d)


def find_pseudopotential_null(
    phi_ps: np.ndarray,
    x_1d_um: np.ndarray,
    y_1d_um: np.ndarray,
    guess_x_um: float = 0.0,
    guess_y_um: float = 0.0,
    null_search_um: float = 10.0,
) -> Tuple[float, float, float]:
    """Local minimum of phi_ps near the nominal ion position in the chip plane."""
    xg, yg = np.meshgrid(x_1d_um, y_1d_um, indexing="xy")
    mask = (
        (np.abs(xg - guess_x_um) <= null_search_um)
        & (np.abs(yg - guess_y_um) <= null_search_um)
    )
    if not np.any(mask):
        idx = np.unravel_index(np.nanargmin(phi_ps), phi_ps.shape)
    else:
        tmp = np.where(mask, phi_ps, np.nan)
        idx = np.unravel_index(np.nanargmin(tmp), phi_ps.shape)
    null_x = float(xg[idx])
    null_y = float(yg[idx])
    ps_min = float(phi_ps[idx])
    return null_x, null_y, ps_min


def fit_multipoles(
    v: np.ndarray,
    x_1d_um: np.ndarray,
    y_1d_um: np.ndarray,
    x0: float,
    y0: float,
    r_fit: float,
    r_norm: float,
    n_max: int = 8,
    n_theta: int = 512,
) -> Dict[int, float]:
    """Circular Fourier multipole fit (same convention as the notebook)."""
    xg, yg = np.meshgrid(x_1d_um, y_1d_um, indexing="xy")
    interp = RegularGridInterpolator(
        (yg[:, 0], xg[0, :]), v, method="cubic", bounds_error=False, fill_value=0.0
    )
    theta = np.linspace(0, 2 * np.pi, n_theta, endpoint=False)
    pts = np.column_stack([y0 + r_fit * np.sin(theta), x0 + r_fit * np.cos(theta)])
    vc = interp(pts)
    fft = np.fft.fft(vc) / n_theta
    p: Dict[int, float] = {}
    for n in range(n_max + 1):
        if n == 0:
            an, bn = float(np.real(fft[0])), 0.0
        else:
            an = 2.0 * float(np.real(fft[n]))
            bn = -2.0 * float(np.imag(fft[n]))
        amp = float(np.hypot(an, bn))
        scale = (r_fit / r_norm) ** n if n > 0 else 1.0
        p[n] = amp / scale
    return p


def ratio_row(p: Dict[int, float], base: int = 2, hi: int = 8) -> Dict[str, float]:
    p2 = p.get(base, 0.0)
    return {f"p{n}/p{base}": (p[n] / p2 if p2 else np.nan) for n in range(base + 1, hi + 1)}


def fit_anharmonicity_multipoles(
    phi_ps_shifted: np.ndarray,
    x_1d_um: np.ndarray,
    y_1d_um: np.ndarray,
    null_x_um: float,
    null_y_um: float,
    electrodes: Sequence[dict],
    n_max: int = 8,
) -> Tuple[Dict[int, float], Dict[str, float], float, float]:
    """Fit multipoles on shifted pseudopotential centered at the refined null."""
    r_norm = ion_electrode_dist(electrodes, null_x_um, null_y_um)
    r_fit = max(r_norm * 0.6, 3.0 * (x_1d_um[1] - x_1d_um[0]))
    r_norm = max(r_norm, r_fit)
    ps_p = fit_multipoles(
        phi_ps_shifted, x_1d_um, y_1d_um, null_x_um, null_y_um, r_fit, r_norm, n_max=n_max
    )
    return ps_p, ratio_row(ps_p), r_norm, r_fit


def cartesian_taylor_coefficients(
    phi_ps_shifted: np.ndarray,
    x_1d_um: np.ndarray,
    y_1d_um: np.ndarray,
    x0_um: float,
    y0_um: float,
    r_fit: float,
    order: int = 4,
) -> Dict[str, float]:
    """
    Local 2D Taylor fit: Phi ~ sum c_ij (x-x0)^i (y-y0)^j  for i+j <= order.
    Returns curvatures and dimensionless anharmonicity ratios.
    """
    xg, yg = np.meshgrid(x_1d_um, y_1d_um, indexing="xy")
    mask = (xg - x0_um) ** 2 + (yg - y0_um) ** 2 <= r_fit**2
    xs = (xg[mask] - x0_um) * UM
    ys = (yg[mask] - y0_um) * UM
    zs = phi_ps_shifted[mask]
    if zs.size < 6:
        return {k: np.nan for k in ("k_x", "k_y", "c40_over_c20_sq", "c04_over_c02_sq", "c30", "c03")}

    monomials: List[Tuple[int, int]] = []
    for total in range(order + 1):
        for i in range(total, -1, -1):
            j = total - i
            monomials.append((i, j))

    a = np.column_stack([(xs**i) * (ys**j) for i, j in monomials])
    coeff, _, _, _ = np.linalg.lstsq(a, zs, rcond=None)
    c: Dict[Tuple[int, int], float] = {monomials[k]: float(coeff[k]) for k in range(len(monomials))}

    k_x = 2.0 * c.get((2, 0), 0.0)
    k_y = 2.0 * c.get((0, 2), 0.0)
    c20 = c.get((2, 0), np.nan)
    c02 = c.get((0, 2), np.nan)
    c40 = c.get((4, 0), np.nan)
    c04 = c.get((0, 4), np.nan)

    return {
        "k_x": k_x,
        "k_y": k_y,
        "c30": c.get((3, 0), np.nan),
        "c03": c.get((0, 3), np.nan),
        "c40_over_c20_sq": (c40 / c20**2) if c20 else np.nan,
        "c04_over_c02_sq": (c04 / c02**2) if c02 else np.nan,
    }


def grid_extent_from_electrodes(
    electrodes: Sequence[dict],
    margin_um: float = 40.0,
) -> Tuple[float, float, float, float]:
    all_pts = np.vstack([np.asarray(e["poly"], dtype=float) for e in electrodes if e.get("poly")])
    return (
        float(all_pts[:, 0].min() - margin_um),
        float(all_pts[:, 0].max() + margin_um),
        float(all_pts[:, 1].min() - margin_um),
        float(all_pts[:, 1].max() + margin_um),
    )


def analyze_sketch_trap_solid_angle(
    electrodes: Sequence[dict],
    theta_deg: float,
    z_ion_um: float = 30.0,
    grid_points: int = 201,
    null_search_um: float = 10.0,
    margin_um: float = 40.0,
) -> dict:
    """Full solid-angle analysis for one sketch geometry."""
    xmin, xmax, ymin, ymax = grid_extent_from_electrodes(electrodes, margin_um)
    x_1d = np.linspace(xmin, xmax, grid_points)
    y_1d = np.linspace(ymin, ymax, grid_points)

    xg, yg, phi_rf = phi_rf_grid_vectorized(x_1d, y_1d, z_ion_um, electrodes)
    phi_ps = pseudopotential_from_phi_rf(phi_rf, x_1d, y_1d)

    null_x, null_y, ps_min = find_pseudopotential_null(
        phi_ps, x_1d, y_1d, guess_x_um=0.0, guess_y_um=0.0, null_search_um=null_search_um
    )
    phi_ps_shifted = phi_ps - ps_min

    r_norm_guess = ion_electrode_dist(electrodes, null_x, null_y)
    r_fit_rf = max(r_norm_guess * 0.6, 3.0 * (x_1d[1] - x_1d[0]))
    r_norm_rf = max(r_norm_guess, r_fit_rf)
    rf_p = fit_multipoles(phi_rf, x_1d, y_1d, null_x, null_y, r_fit_rf, r_norm_rf)
    rf_rat = ratio_row(rf_p)

    ps_p, ps_rat, r_norm, r_fit = fit_anharmonicity_multipoles(
        phi_ps_shifted, x_1d, y_1d, null_x, null_y, electrodes
    )
    taylor = cartesian_taylor_coefficients(phi_ps_shifted, x_1d, y_1d, null_x, null_y, r_fit)

    return {
        "theta_deg": theta_deg,
        "z_ion_um": z_ion_um,
        "null_x_um": null_x,
        "null_y_um": null_y,
        "nearest_electrode_R_um": r_norm,
        "r_fit_um": r_fit,
        "phi_ps_min_V": ps_min,
        "rf_p": rf_p,
        "rf_ratios": rf_rat,
        "ps_p": ps_p,
        "ps_ratios": ps_rat,
        "taylor": taylor,
        "x_1d": x_1d,
        "y_1d": y_1d,
        "phi_rf": phi_rf,
        "phi_ps_shifted": phi_ps_shifted,
    }


def _row_from_result(res: dict) -> dict:
    row = {
        "theta_deg": res["theta_deg"],
        "z_ion_um": res["z_ion_um"],
        "null_x_um": res["null_x_um"],
        "null_y_um": res["null_y_um"],
        "R_um": res["nearest_electrode_R_um"],
        "r_fit_um": res["r_fit_um"],
        "phi_ps_min_V": res["phi_ps_min_V"],
        "phi_rf_p2": res["rf_p"].get(2, np.nan),
        "phi_ps_p2": res["ps_p"].get(2, np.nan),
    }
    for prefix, rat in (("phi_rf", res["rf_ratios"]), ("phi_ps", res["ps_ratios"])):
        for k, v in rat.items():
            row[f"{prefix}_{k}"] = v
    for k, v in res["taylor"].items():
        row[f"taylor_{k}"] = v
    return row


def run_sketch_solid_angle_sweep(
    generate_trap_geometry,
    angles: Iterable[float] = SKETCH_TRAP_ANGLES,
    z_ion_um: float = 30.0,
    grid_points: int = 201,
    null_search_um: float = 10.0,
    save: bool = True,
    plot: bool = True,
) -> pd.DataFrame:
    """
    Run solid-angle anharmonicity analysis for each sketch angle.

    Parameters
    ----------
    generate_trap_geometry : callable
        Notebook function generate_trap_geometry(theta_degrees, ...).
    """
    os.makedirs("csv", exist_ok=True)
    os.makedirs("pngs", exist_ok=True)

    rows = []
    results = []
    for theta in angles:
        geom = generate_trap_geometry(float(theta), outer_pad_contact_gap=0.0)
        electrodes = geom["electrodes"]
        res = analyze_sketch_trap_solid_angle(
            electrodes,
            theta_deg=float(theta),
            z_ion_um=z_ion_um,
            grid_points=grid_points,
            null_search_um=null_search_um,
        )
        results.append(res)
        rows.append(_row_from_result(res))
        print(f"theta={theta:g} deg  null=({res['null_x_um']:.2f}, {res['null_y_um']:.2f}) um")
        print(f"  phi_ps p4/p2={res['ps_ratios'].get('p4/p2', np.nan):.4f}  "
              f"p6/p2={res['ps_ratios'].get('p6/p2', np.nan):.4f}")

    df = pd.DataFrame(rows)
    if save:
        df.to_csv("csv/sketch_trap_anharmonicity_solid_angle.csv", index=False)

    if plot:
        plot_anharmonicity_vs_theta(df, save=save)

    return df


def plot_anharmonicity_vs_theta(df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Plot pseudopotential multipole ratios vs sketch angle."""
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    for col, label in (("phi_ps_p4/p2", "p4/p2"), ("phi_ps_p6/p2", "p6/p2"), ("phi_ps_p3/p2", "p3/p2")):
        if col in df.columns:
            ax.plot(df["theta_deg"], df[col], "o-", lw=1.8, ms=6, label=label)
    ax.set_xlabel(r"$\theta$ (deg)")
    ax.set_ylabel(r"multipole ratio $p_n/p_2$ (pseudopotential)")
    ax.set_title("Solid-angle anharmonicity vs RF angle")
    ax.grid(True, alpha=0.35)
    ax.legend(fontsize=9)
    plt.tight_layout()
    if save:
        fig.savefig("pngs/sketch_trap_anharmonicity_vs_theta.png", dpi=200, bbox_inches="tight")
    return fig


def validate_solid_angle_square(size_um: float = 200.0, height_um: float = 30.0) -> float:
    """
    Sanity check: large square electrode at V=1 should give phi ~ V directly above center.
    Returns relative error |phi - V| / V.
    """
    half = size_um / 2.0
    square = [(-half, -half), (half, -half), (half, half), (-half, half)]
    elec = {"V": 1.0, "poly": square}
    fp = field_point_3d(0.0, 0.0, height_um)
    phi = electrode_potential(elec, fp)
    return abs(phi - 1.0)
