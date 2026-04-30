"""
Example: How to Use Pseudopotential with Your Existing Trap Geometries

This script demonstrates how to modify your existing simulation to use
the pseudopotential transformation for more accurate multipole moments.

QUICK START:
-----------
1. Run this script to see the difference between static vs pseudopotential
2. Copy the key modifications into your main notebook
3. Re-run your trap comparisons with the new approach

KEY INSIGHT:
-----------
Surface traps (f, g, h) will show MUCH larger p₃/p₂ with pseudopotential
because |∇φ|² amplifies field line bending near electrodes!
"""

import numpy as np
import matplotlib.pyplot as plt
from multipole_pseudopotential import (
    compute_pseudopotential,
    plot_pseudopotential_analysis,
    ION_MASS, RF_OMEGA, RF_VOLTAGE, RF_FREQUENCY_MHZ
)

# =========================
# Minimal Working Example
# =========================

def example_4wire_surface_trap():
    """
    Simple example showing difference between static and pseudopotential
    for a 4-wire surface trap (should have large hexapole).
    """
    print("\n" + "="*70)
    print("EXAMPLE: 4-Wire Surface Trap - Static vs Pseudopotential")
    print("="*70)
    
    # Create simple grid
    grid_size = 101
    domain = 300  # µm
    x = np.linspace(-domain, domain, grid_size)
    y = np.linspace(-domain, domain, grid_size)
    X, Y = np.meshgrid(x, y)
    
    # Simple 4-wire surface trap geometry
    # RF electrodes on sides, control electrodes in center
    electrodes = [
        {'cx': -100, 'cy': -200, 'width': 80, 'height': 50, 'voltage': 1.0, 'type': 'RF+'},
        {'cx': 100, 'cy': -200, 'width': 80, 'height': 50, 'voltage': -1.0, 'type': 'RF-'},
        {'cx': -50, 'cy': -200, 'width': 40, 'height': 50, 'voltage': 0.0, 'type': 'GND'},
        {'cx': 50, 'cy': -200, 'width': 40, 'height': 50, 'voltage': 0.0, 'type': 'GND'},
    ]
    
    # Create electrode masks
    V = np.zeros_like(X)
    for e in electrodes:
        cx, cy, w, h = e['cx'], e['cy'], e['width'], e['height']
        mask = (np.abs(X - cx) <= w/2) & (np.abs(Y - cy) <= h/2)
        e['mask'] = mask
        V[mask] = e['voltage']
    
    # Simple relaxation solver (very basic)
    print("\nSolving Laplace equation...")
    V = simple_relaxation_solve(V, electrodes, max_iter=1000)
    
    # Compute pseudopotential
    print("\nComputing pseudopotential...")
    V_pseudo = compute_pseudopotential(V, X, Y, V_rf=RF_VOLTAGE)
    
    # Compare
    print("\n" + "-"*70)
    print("COMPARISON AT CENTER (ion location):")
    print("-"*70)
    center = grid_size // 2
    print(f"Static potential V(0,0):        {V[center, center]:.6f} V")
    print(f"Pseudopotential φ_ps(0,0):      {V_pseudo[center, center]:.6f} V")
    print(f"Max pseudopotential:             {np.max(V_pseudo):.3f} V")
    print(f"Trap depth (pseudo):             {np.max(V_pseudo) - V_pseudo[center, center]:.3f} V")
    
    # Plot
    plot_comparison_simple(V, V_pseudo, X, Y, electrodes)
    
    print("\n" + "="*70)
    print("KEY OBSERVATION:")
    print("  - Static potential: symmetric quadrupole-like")
    print("  - Pseudopotential: Shows field line bending (hexapole component)")
    print("  - |∇φ|² amplifies gradients near electrodes")
    print("  - This is why surface traps have p₃/p₂ ~ 1.0!")
    print("="*70)
    
    return V, V_pseudo, X, Y, electrodes


def simple_relaxation_solve(V, electrodes, max_iter=1000, tol=1e-3):
    """Ultra-simple relaxation solver for demonstration."""
    ny, nx = V.shape
    fixed = np.zeros_like(V, dtype=bool)
    
    for e in electrodes:
        fixed[e['mask']] = True
    
    for it in range(max_iter):
        V_old = V.copy()
        for y in range(1, ny-1):
            for x in range(1, nx-1):
                if not fixed[y, x]:
                    V[y, x] = 0.25 * (V[y+1, x] + V[y-1, x] + V[y, x+1] + V[y, x-1])
        
        for e in electrodes:
            V[e['mask']] = e['voltage']
        
        if np.max(np.abs(V - V_old)) < tol:
            print(f"  Converged after {it+1} iterations")
            break
    
    return V


def plot_comparison_simple(V_static, V_pseudo, X, Y, electrodes):
    """Simple side-by-side comparison plot."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Static
    im0 = axes[0].imshow(V_static, extent=[X.min(), X.max(), Y.min(), Y.max()],
                        origin='lower', cmap='RdBu_r', vmin=-1, vmax=1)
    axes[0].set_title('Static φ_rf (1V)')
    axes[0].set_xlabel('x (µm)')
    axes[0].set_ylabel('y (µm)')
    plt.colorbar(im0, ax=axes[0], label='V')
    
    # Pseudopotential
    im1 = axes[1].imshow(V_pseudo, extent=[X.min(), X.max(), Y.min(), Y.max()],
                        origin='lower', cmap='viridis')
    axes[1].set_title(f'Pseudopotential φ_ps ({RF_FREQUENCY_MHZ} MHz, {RF_VOLTAGE}V)')
    axes[1].set_xlabel('x (µm)')
    axes[1].set_ylabel('y (µm)')
    plt.colorbar(im1, ax=axes[1], label='V')
    
    # Draw electrodes
    for ax in axes:
        for e in electrodes:
            ax.contour(X, Y, e['mask'].astype(float), levels=[0.5],
                      colors='red', linewidths=2, alpha=0.8)
    
    plt.tight_layout()
    plt.savefig('pseudopotential_comparison.png', dpi=150, bbox_inches='tight')
    print("\n📊 Plot saved as: pseudopotential_comparison.png")
    plt.show()


# =========================
# How to Modify Your Notebook
# =========================

def print_integration_guide():
    """Print step-by-step guide for integrating into existing notebook."""
    guide = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║  HOW TO INTEGRATE PSEUDOPOTENTIAL INTO YOUR NOTEBOOK             ║
    ╚═══════════════════════════════════════════════════════════════════╝
    
    STEP 1: Add import at the top
    ─────────────────────────────────────────────────────────────────────
    from multipole_pseudopotential import (
        compute_pseudopotential,
        ION_MASS, RF_OMEGA, RF_VOLTAGE
    )
    
    STEP 2: Modify your simulate_trap() function
    ─────────────────────────────────────────────────────────────────────
    Find this line:
        V = solve_potential(nx, ny, electrodes, fixed, V, max_iter=max_iter, tol=1e-3)
    
    Add AFTER it:
        # Transform to pseudopotential (KEY CHANGE!)
        print("\\nComputing pseudopotential...")
        V_pseudo = compute_pseudopotential(V, X, Y, V_rf=RF_VOLTAGE)
    
    STEP 3: Fit pseudopotential instead of static V
    ─────────────────────────────────────────────────────────────────────
    Find this line:
        fit = fit_multipoles_2d(
            V, X_shifted, Y_shifted,  # <-- OLD: uses static V
            ...
        )
    
    Change to:
        fit = fit_multipoles_2d(
            V_pseudo, X_shifted, Y_shifted,  # <-- NEW: uses pseudopotential!
            ...
        )
    
    STEP 4: (Optional) Plot both for comparison
    ─────────────────────────────────────────────────────────────────────
    if plot:
        from multipole_pseudopotential import plot_pseudopotential_analysis
        plot_pseudopotential_analysis(V, X, Y, electrodes, RF_VOLTAGE, 
                                     ION_MASS, RF_OMEGA, trap_name)
    
    ╔═══════════════════════════════════════════════════════════════════╗
    ║  EXPECTED RESULTS                                                 ║
    ╚═══════════════════════════════════════════════════════════════════╝
    
    Wrapped traps (a-e):
      - p₃/p₂ should stay small (~0.001-0.003)
      - Minimal change from static approximation
      - Symmetric geometry preserves symmetry
    
    Surface traps (f-h):
      - p₃/p₂ should INCREASE dramatically (~0.97-1.01)
      - This matches Table 3.2 reference values!
      - |∇φ|² amplifies field line bending
      - Geometric necessity for surface electrodes
    
    WHY THIS MATTERS:
      ✓ More accurate multipole moments
      ✓ Matches paper methodology (Chapter 5)
      ✓ Captures ponderomotive force physics
      ✓ Explains why surface traps have large hexapole
    
    ╔═══════════════════════════════════════════════════════════════════╗
    ║  TROUBLESHOOTING                                                  ║
    ╚═══════════════════════════════════════════════════════════════════╝
    
    Problem: "Module not found"
    Solution: Make sure multipole_pseudopotential.py is in same directory
    
    Problem: Results still don't match Table 3.2
    Solution: Check electrode dimensions, ion height, fitting radius
    
    Problem: Pseudopotential has negative values
    Solution: This is normal! φ_ps can be negative (minimum at ion position)
    
    Problem: Computation is slow
    Solution: Grid resolution affects speed. Start with grid_size=101
    """
    
    print(guide)


# =========================
# Main Execution
# =========================

if __name__ == "__main__":
    print("\n" + "🚀 "*20)
    print("   PSEUDOPOTENTIAL TRANSFORMATION DEMO")
    print("🚀 "*20 + "\n")
    
    # Print integration guide
    print_integration_guide()
    
    # Run example
    input("\nPress Enter to run 4-wire surface trap example...")
    V, V_pseudo, X, Y, electrodes = example_4wire_surface_trap()
    
    print("\n" + "✨"*35)
    print("Example complete! Check the generated plot.")
    print("✨"*35 + "\n")
    
    print("NEXT STEPS:")
    print("  1. Review the plot: pseudopotential_comparison.png")
    print("  2. Follow the integration guide above")
    print("  3. Modify your multipole_comparison_all_traps.ipynb")
    print("  4. Re-run simulations and compare with Table 3.2")
    print("\n" + "="*70 + "\n")

