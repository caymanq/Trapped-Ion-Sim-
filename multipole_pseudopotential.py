"""
Multipole Moment Extraction with RF Pseudopotential Transformation

This module implements the pseudopotential approach (Eq. 5.2) for accurate
multipole moment calculation in ion trap geometries.

Key Equation:
    φ_ps(r) = (q / (4 * m * Ω²_rf)) * |V_rf * ∇φ_rf(r)|²

Usage:
    1. Solve ∇²V=0 for static RF potential (φ_rf at 1V)
    2. Transform to pseudopotential using compute_pseudopotential()
    3. Fit pseudopotential to multipole expansion
    4. Extract p_N/p_2 ratios

Author: Generated for ion trap simulation
Date: 2026-01-01
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.constants import atomic_mass, elementary_charge
from tqdm import tqdm

# =========================
# Physical Constants
# =========================

# Ion parameters (¹⁷¹Yb⁺ - commonly used in NIST traps)
ION_MASS_AMU = 171  # atomic mass units
ION_MASS = ION_MASS_AMU * atomic_mass  # kg
ION_CHARGE = elementary_charge  # C

# RF parameters (typical for NIST-style traps)
RF_FREQUENCY_MHZ = 30.0  # MHz (typical range: 10-50 MHz)
RF_OMEGA = 2 * np.pi * RF_FREQUENCY_MHZ * 1e6  # rad/s
RF_VOLTAGE = 500.0  # V (peak voltage, typical range: 100-1000 V)


# =========================
# Core Functions
# =========================

def compute_pseudopotential(V, X, Y, V_rf=RF_VOLTAGE, m_ion=ION_MASS, 
                           Omega_rf=RF_OMEGA, q=elementary_charge):
    """
    Convert static RF potential to pseudopotential using Eq. 5.2:
    
    φ_ps(r) = (q / (4 * m * Ω²_rf)) * |V_rf * ∇φ_rf(r)|²
    
    This transformation captures the ponderomotive force that ions experience
    in a time-averaged RF potential. The pseudopotential includes nonlinear
    effects from the squared gradient that static approximations miss.
    
    Parameters:
    -----------
    V : 2D numpy array
        Static potential φ_rf calculated at 1V (dimensionless)
        Obtained by solving ∇²V = 0 with RF electrodes at ±1V
    X, Y : 2D numpy arrays
        Coordinate grids in µm (micrometers)
    V_rf : float, optional
        Peak RF voltage in Volts (default: 500V)
    m_ion : float, optional
        Ion mass in kg (default: ¹⁷¹Yb⁺ mass)
    Omega_rf : float, optional
        RF angular frequency in rad/s (default: 2π×30 MHz)
    q : float, optional
        Ion charge in Coulombs (default: elementary charge)
    
    Returns:
    --------
    phi_ps : 2D numpy array
        Pseudopotential in Volts
        This is what the ion actually "feels" in the time-averaged sense
    
    Notes:
    ------
    - The gradient is computed in SI units (V/m) for proper dimensional analysis
    - The |∇φ|² term amplifies field inhomogeneities
    - This is why surface traps have much larger hexapole moments!
    - Field line bending near electrodes → large |∇φ|² → large p₃/p₂
    
    Example:
    --------
    >>> V_static = solve_laplace(electrodes)  # φ_rf at 1V
    >>> V_pseudo = compute_pseudopotential(V_static, X, Y)
    >>> # Now fit V_pseudo (not V_static!) to multipoles
    >>> fit = fit_multipoles_2d(V_pseudo, X, Y)
    """
    # Compute grid spacing (convert µm to m for proper SI units)
    dx_um = X[0, 1] - X[0, 0]  # µm
    dy_um = Y[1, 0] - Y[0, 0]  # µm
    dx_m = dx_um * 1e-6  # m
    dy_m = dy_um * 1e-6  # m
    
    # Compute gradient of φ_rf using centered differences
    # np.gradient returns [∂V/∂y, ∂V/∂x] for 2D arrays
    # Units: (V) / (m) = V/m (electric field)
    grad_y, grad_x = np.gradient(V, dy_m, dx_m)
    
    # Compute |V_rf * ∇φ_rf|² 
    # Units: (V)² × (V/m)² = V⁴/m²
    # This is the squared electric field amplitude
    grad_V_squared = (V_rf * grad_x)**2 + (V_rf * grad_y)**2
    
    # Apply pseudopotential formula (Eq. 5.2)
    # Units: (C) / (kg × (rad/s)²) × (V⁴/m²)
    #      = (C × V) / (kg × s⁻² × m²)
    #      = J / (kg × m²/s²)
    #      = V  ✓ (correct dimensional analysis)
    phi_ps = (q / (4 * m_ion * Omega_rf**2)) * grad_V_squared
    
    return phi_ps


def compute_pseudopotential_with_diagnostics(V, X, Y, V_rf=RF_VOLTAGE, 
                                             m_ion=ION_MASS, Omega_rf=RF_OMEGA):
    """
    Same as compute_pseudopotential but returns additional diagnostic info.
    
    Returns:
    --------
    phi_ps : 2D array
        Pseudopotential (V)
    grad_x, grad_y : 2D arrays
        Electric field components (V/m) at 1V
    E_magnitude : 2D array
        Electric field magnitude (V/m) at actual V_rf
    diagnostics : dict
        Contains useful statistics
    """
    dx_um = X[0, 1] - X[0, 0]
    dy_um = Y[1, 0] - Y[0, 0]
    dx_m = dx_um * 1e-6
    dy_m = dy_um * 1e-6
    
    grad_y, grad_x = np.gradient(V, dy_m, dx_m)
    
    # Electric field at actual V_rf
    E_x = V_rf * grad_x
    E_y = V_rf * grad_y
    E_magnitude = np.sqrt(E_x**2 + E_y**2)
    
    grad_V_squared = E_x**2 + E_y**2
    phi_ps = (elementary_charge / (4 * m_ion * Omega_rf**2)) * grad_V_squared
    
    diagnostics = {
        'max_E_field': np.max(E_magnitude),
        'max_pseudopot': np.max(phi_ps),
        'min_pseudopot': np.min(phi_ps),
        'pseudopot_depth': np.max(phi_ps) - np.min(phi_ps),
        'center_pseudopot': phi_ps[len(phi_ps)//2, len(phi_ps[0])//2]
    }
    
    return phi_ps, grad_x, grad_y, E_magnitude, diagnostics


def plot_pseudopotential_analysis(V_static, X, Y, electrodes, V_rf=RF_VOLTAGE,
                                  m_ion=ION_MASS, Omega_rf=RF_OMEGA, 
                                  trap_name="Ion Trap"):
    """
    Comprehensive visualization comparing static vs pseudopotential.
    
    Creates a 4-panel figure showing:
    1. Static potential φ_rf
    2. Electric field magnitude
    3. Pseudopotential φ_ps
    4. Pseudopotential along x-axis cut
    """
    # Compute pseudopotential and diagnostics
    phi_ps, grad_x, grad_y, E_mag, diag = compute_pseudopotential_with_diagnostics(
        V_static, X, Y, V_rf, m_ion, Omega_rf
    )
    
    fig = plt.figure(figsize=(18, 10))
    
    # 1. Static potential
    ax1 = plt.subplot(2, 3, 1)
    im1 = ax1.imshow(V_static, extent=[X.min(), X.max(), Y.min(), Y.max()],
                     origin='lower', cmap='RdBu_r', vmin=-1, vmax=1)
    ax1.set_title(f'{trap_name}\nStatic φ_rf (at 1V)')
    ax1.set_xlabel('x (µm)')
    ax1.set_ylabel('y (µm)')
    plt.colorbar(im1, ax=ax1, label='Potential (V)')
    
    # Draw electrodes
    for e in electrodes:
        ax1.contour(X, Y, e['mask'].astype(float), levels=[0.5],
                   colors='black', linewidths=2, alpha=0.7)
    
    # 2. Electric field magnitude
    ax2 = plt.subplot(2, 3, 2)
    im2 = ax2.imshow(E_mag, extent=[X.min(), X.max(), Y.min(), Y.max()],
                     origin='lower', cmap='hot')
    ax2.set_title(f'Electric Field |E|\n(at V_rf = {V_rf}V)')
    ax2.set_xlabel('x (µm)')
    ax2.set_ylabel('y (µm)')
    plt.colorbar(im2, ax=ax2, label='|E| (V/m)')
    
    for e in electrodes:
        ax2.contour(X, Y, e['mask'].astype(float), levels=[0.5],
                   colors='cyan', linewidths=2, alpha=0.7)
    
    # 3. Pseudopotential
    ax3 = plt.subplot(2, 3, 3)
    im3 = ax3.imshow(phi_ps, extent=[X.min(), X.max(), Y.min(), Y.max()],
                     origin='lower', cmap='viridis')
    ax3.set_title(f'Pseudopotential φ_ps\n(Ω_rf = {RF_FREQUENCY_MHZ} MHz)')
    ax3.set_xlabel('x (µm)')
    ax3.set_ylabel('y (µm)')
    plt.colorbar(im3, ax=ax3, label='φ_ps (V)')
    
    for e in electrodes:
        ax3.contour(X, Y, e['mask'].astype(float), levels=[0.5],
                   colors='red', linewidths=2, alpha=0.7)
    
    # 4. Line cut through center (x-axis)
    ax4 = plt.subplot(2, 3, 4)
    center_y = len(V_static) // 2
    x_line = X[center_y, :]
    V_line = V_static[center_y, :]
    ax4.plot(x_line, V_line, 'b-', linewidth=2, label='Static φ_rf')
    ax4.set_xlabel('x (µm)')
    ax4.set_ylabel('Potential (V)')
    ax4.set_title('x-axis cut (y=0)')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    ax4.axhline(0, color='k', linestyle='--', alpha=0.3)
    
    # 5. Pseudopotential line cut
    ax5 = plt.subplot(2, 3, 5)
    phi_ps_line = phi_ps[center_y, :]
    ax5.plot(x_line, phi_ps_line, 'r-', linewidth=2, label='Pseudopotential')
    ax5.set_xlabel('x (µm)')
    ax5.set_ylabel('φ_ps (V)')
    ax5.set_title('Pseudopotential x-axis cut')
    ax5.grid(True, alpha=0.3)
    ax5.legend()
    
    # 6. Diagnostics text
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    
    diag_text = f"""
    PSEUDOPOTENTIAL DIAGNOSTICS
    {'='*40}
    
    RF Parameters:
      Frequency: {RF_FREQUENCY_MHZ} MHz
      Ω_rf: {Omega_rf:.3e} rad/s
      V_rf: {V_rf} V
    
    Ion: ¹⁷¹Yb⁺
      Mass: {m_ion:.3e} kg
      Charge: {elementary_charge:.3e} C
    
    Results:
      Max |E|: {diag['max_E_field']:.3e} V/m
      φ_ps (max): {diag['max_pseudopot']:.3f} V
      φ_ps (min): {diag['min_pseudopot']:.3f} V
      Trap depth: {diag['pseudopot_depth']:.3f} V
      φ_ps (center): {diag['center_pseudopot']:.6f} V
    
    Note: Fit φ_ps (not V_static) to 
    extract accurate multipole moments!
    """
    
    ax6.text(0.1, 0.5, diag_text, fontfamily='monospace', 
             fontsize=10, verticalalignment='center')
    
    plt.tight_layout()
    return fig, phi_ps, diag


# =========================
# Integration with existing code
# =========================

def simulate_trap_with_pseudopotential(trap_builder, trap_name, grid_size=201, 
                                      domain_scale=1.0, max_iter=5000, 
                                      V_rf=RF_VOLTAGE, plot=True):
    """
    Modified simulation function that uses pseudopotential.
    
    This should replace your existing simulate_trap() function.
    Key difference: fits pseudopotential instead of static potential.
    """
    from tqdm import tqdm  # Ensure tqdm is available
    
    print(f"\n{'='*60}")
    print(f"Simulating: {trap_name} (with pseudopotential)")
    print(f"{'='*60}")
    
    # ... (rest of your grid setup code here)
    # This function would need the full implementation from your notebook
    # I'm providing the key modification point:
    
    # After solving static potential V:
    # V = solve_potential(nx, ny, electrodes, fixed, V, max_iter=max_iter, tol=1e-4)
    
    # *** KEY CHANGE: Transform to pseudopotential ***
    print("\nTransforming to pseudopotential...")
    V_pseudo = compute_pseudopotential(V, X, Y, V_rf=V_rf)
    
    # *** FIT PSEUDOPOTENTIAL (not static V) ***
    fit = fit_multipoles_2d(
        V_pseudo,  # <-- Use pseudopotential here!
        X_shifted, 
        Y_shifted,
        r_fit_um=r_fit,
        ion_elc_dis_um=ion_elc_dis,
        n_max=8,
        exclude_mask=exclude_mask
    )
    
    # Rest of your analysis code...
    
    if plot:
        plot_pseudopotential_analysis(V, X, Y, electrodes, V_rf, 
                                     ION_MASS, RF_OMEGA, trap_name)
    
    return fit


# =========================
# Example Usage
# =========================

if __name__ == "__main__":
    print("RF Pseudopotential Module Loaded")
    print("="*60)
    print(f"Default Parameters:")
    print(f"  Ion: ¹⁷¹Yb⁺ ({ION_MASS_AMU} amu)")
    print(f"  RF Frequency: {RF_FREQUENCY_MHZ} MHz")
    print(f"  RF Voltage: {RF_VOLTAGE} V")
    print(f"  Ion Mass: {ION_MASS:.3e} kg")
    print(f"  RF Ω: {RF_OMEGA:.3e} rad/s")
    print("="*60)
    print("\nKey Functions:")
    print("  - compute_pseudopotential(V, X, Y)")
    print("  - compute_pseudopotential_with_diagnostics(V, X, Y)")
    print("  - plot_pseudopotential_analysis(V, X, Y, electrodes)")
    print("\nUsage:")
    print("  1. Solve ∇²V=0 for static potential")
    print("  2. V_pseudo = compute_pseudopotential(V, X, Y)")
    print("  3. fit = fit_multipoles_2d(V_pseudo, X, Y)  # Use V_pseudo!")
    print("  4. Extract p_n/p_2 ratios")

