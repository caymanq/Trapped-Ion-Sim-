"""Physical constants and defaults used by the ion-trap solvers."""

from math import pi

ELEMENTARY_CHARGE = 1.602176634e-19
ATOMIC_MASS = 1.66053906660e-27

# Representative Be+ defaults used by the notebooks.
ION_MASS_AMU = 9.0121831
ION_MASS_KG = ION_MASS_AMU * ATOMIC_MASS
RF_VOLTAGE = 500.0
RF_FREQUENCY_HZ = 30.0e6
RF_OMEGA = 2.0 * pi * RF_FREQUENCY_HZ

DEFAULT_DOMAIN_UM = 500.0
DEFAULT_GRID_SIZE = 121
PHYSICS_TOL = 1.0e-3
