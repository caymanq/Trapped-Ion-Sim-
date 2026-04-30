"""
Simple test: 2D quadrupole trap with correct multipole extraction
"""
import numpy as np
import matplotlib.pyplot as plt

# Simple 4-electrode trap (like a linear Paul trap cross-section)
# Electrodes at corners create quadrupole field
def create_simple_quadrupole():
    """
    Four electrodes arranged in a square:
    - Two at V=+1 (diagonal)
    - Two at V=-1 (other diagonal)
    Creates saddle potential with RF null at center
    """
    electrodes = []
    d = 1.0  # Distance from center to electrode
    w = 0.1  # Electrode width
    
    # Diagonal 1: +V
    electrodes.append((d-w, d+w, d-w, d+w, 1.0))    # Top-right
    electrodes.append((-d-w, -d+w, -d-w, -d+w, 1.0))  # Bottom-left
    
    # Diagonal 2: -V  
    electrodes.append((-d-w, -d+w, d-w, d+w, -1.0))  # Top-left
    electrodes.append((d-w, d+w, -d-w, -d+w, -1.0))  # Bottom-right
    
    return electrodes, np.array([0.0, 0.0])

def solve_laplace_sor(electrodes, grid_size=301, domain=2.5, omega=1.9, max_iter=20000, tol=1e-7):
    """Solve Laplace equation with SOR"""
    x = np.linspace(-domain, domain, grid_size)
    y = np.linspace(-domain, domain, grid_size)
    V = np.zeros((grid_size, grid_size))
    is_elec = np.zeros_like(V, dtype=bool)
    
    # Mark electrodes
    for i in range(grid_size):
        for j in range(grid_size):
            for (xmin, xmax, ymin, ymax, Vval) in electrodes:
                if xmin <= x[j] <= xmax and ymin <= y[i] <= ymax:
                    is_elec[i, j] = True
                    V[i, j] = Vval
                    break
    
    # SOR iteration
    for it in range(max_iter):
        V_old = V.copy()
        for i in range(1, grid_size-1):
            for j in range(1, grid_size-1):
                if not is_elec[i, j]:
                    V_new = 0.25 * (V[i+1,j] + V[i-1,j] + V[i,j+1] + V[i,j-1])
                    V[i, j] = (1-omega)*V[i,j] + omega*V_new
        
        if it % 1000 == 0:
            err = np.max(np.abs(V - V_old))
            print(f"  Iter {it:5d}, error: {err:.2e}")
            if err < tol:
                print(f"  Converged at {it}")
                break
    
    return V, x, y

def extract_multipoles_disk(V, x, y, center, r_fit, R0=1.0, n_max=8):
    """Extract multipoles by fitting over a disk"""
    X, Y = np.meshgrid(x, y, indexing='xy')
    Xc = X - center[0]
    Yc = Y - center[1]
    R = np.hypot(Xc, Yc)
    
    # Disk mask
    mask = (R <= r_fit) & (np.abs(V) < 0.99)  # Exclude electrodes
    
    xs = Xc[mask].ravel()
    ys = Yc[mask].ravel()
    vs = V[mask].ravel()
    
    print(f"  Fitting with {len(vs)} points in disk r={r_fit}")
    
    # Build design matrix: Re(z^n), Im(z^n) for z=x+iy
    z = xs + 1j*ys
    A_matrix = []
    for n in range(n_max + 1):
        z_pow = z**n / (R0**n)
        A_matrix.append(np.real(z_pow))
        A_matrix.append(np.imag(z_pow))
    
    A_matrix = np.array(A_matrix).T
    coeffs, residuals, rank, s = np.linalg.lstsq(A_matrix, vs, rcond=None)
    
    # Extract multipoles
    multipoles = {'V0': coeffs[0]}
    for n in range(1, n_max+1):
        A_n = coeffs[2*n]
        B_n = coeffs[2*n+1]
        p_n = np.hypot(A_n, B_n)
        multipoles[f'A{n}'] = A_n
        multipoles[f'B{n}'] = B_n
        multipoles[f'p{n}'] = p_n
    
    # Ratios
    p2 = multipoles.get('p2', 1e-15)
    if p2 < 1e-15: p2 = 1e-15
    ratios = {f'p{n}/p2': multipoles[f'p{n}']/p2 for n in range(3, n_max+1)}
    
    return multipoles, ratios

# Main analysis
print("Creating simple quadrupole trap...")
electrodes, center = create_simple_quadrupole()

print("\nSolving Laplace equation...")
V, x, y = solve_laplace_sor(electrodes, grid_size=401, domain=2.5)

print("\nExtracting multipoles...")
R0 = 1.0  # Distance from center to electrodes
r_fit = 0.3  # Fit over disk with radius 30% of R0
multipoles, ratios = extract_multipoles_disk(V, x, y, center, r_fit=r_fit, R0=R0, n_max=8)

print("\nResults:")
print(f"{'Order':<10} {'p_n':<15} {'p_n/p2':<15}")
print("-" * 40)
for n in range(1, 9):
    p_n = multipoles.get(f'p{n}', 0.0)
    ratio = ratios.get(f'p{n}/p2', p_n/multipoles.get('p2', 1))
    print(f"p{n:<9} {p_n:<15.6f} {ratio:<15.6f}")

print("\n✓ For ideal quadrupole: p_n/p_2 should be ~0 for n≠2")
print("  Higher values indicate field imperfections")

# Plot
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# Potential
ax = axes[0]
im = ax.imshow(V, extent=[x[0], x[-1], y[0], y[-1]], origin='lower', cmap='RdBu_r')
ax.plot(0, 0, 'k*', ms=15)
circle = plt.Circle((0, 0), r_fit, fill=False, color='yellow', lw=2, ls='--')
ax.add_patch(circle)
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_title('Potential Field')
plt.colorbar(im, ax=ax)

# Multipole magnitudes
ax = axes[1]
orders = np.arange(1, 9)
mags = [multipoles.get(f'p{n}', 0) for n in orders]
ax.bar(orders, mags, alpha=0.7)
ax.set_xlabel('Order n')
ax.set_ylabel('|p_n|')
ax.set_yscale('log')
ax.set_title('Multipole Magnitudes')
ax.grid(alpha=0.3)

# Ratios
ax = axes[2]
orders = np.arange(3, 9)
ratio_vals = [ratios.get(f'p{n}/p2', 0) for n in orders]
ax.bar(orders, ratio_vals, alpha=0.7, color='orange')
ax.set_xlabel('Order n')
ax.set_ylabel('p_n / p_2')
ax.set_yscale('log')
ax.set_title('Multipole Ratios')
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('simple_trap_test.png', dpi=150)
print("\n✓ Saved plot to simple_trap_test.png")
plt.show()

