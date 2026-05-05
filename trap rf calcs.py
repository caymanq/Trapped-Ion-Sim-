import os
import numpy as np
from scipy import interpolate

import matplotlib.pyplot as plt
import numpy as np
import os
from scipy import interpolate
from scipy.interpolate import UnivariateSpline
import scipy.constants as scipy

from scipy.optimize import curve_fit

import pandas as pd
from io import StringIO
from scipy.optimize import minimize
from sklearn.linear_model import LinearRegression
from scipy.ndimage import rotate


from matplotlib import colors

from scipy.integrate import odeint
from scipy.optimize import minimize, fsolve

# from numba import jit
import time
import os 

from scipy.interpolate import CloughTocher2DInterpolator


# %%

COMSOL_DATA_DIR = "trap sim using COMSOL from IU"


def comsol_data_path(file_name):
    return os.path.join(COMSOL_DATA_DIR, file_name)

folder = 'wheel trap/v0/'
file_name = folder + 'zx_plane_normE_allrf_v03mm_refined2'

data_import = np.loadtxt(file_name, skiprows=8)

# Unravel data
x = np.array(data_import[:,0])
y = np.array(data_import[:,1])
z = np.array(data_import[:,2])
f = np.array(data_import[:,3])

# Format data (for ZX plane)
data = np.array([[x[i],z[i],f[i]] for i in range(len(x))])

# Shift z axis down by 1.5mm
data[:,1] = data[:,1] - 1.5

# Convert mm distances to meter. normE is already V/m
data[:,0] /= 1000
data[:,1] /= 1000

norme_min, norme_max = np.min(data[:,2]), np.max(data[:,2])

# plt.scatter(data[:,0], data[:,1], c=data[:,2], s=0.2)
# plt.tricontour(data[:,0], data[:,1], data[:,2], levels=np.linspace(norme_min, norme_max, 15))
# plt.show()

# Interpolate data
zx_coords = (data[:,0], data[:,1])
rf_upper_right_interp = CloughTocher2DInterpolator(zx_coords, data[:,2])

plt.scatter(data[:,0], data[:,1], c=rf_upper_right_interp(zx_coords), s=0.2)
plt.colorbar()
plt.clim(0, 15000)
plt.show()

# "Trapping" region
xs = 1e-6 * np.linspace(-50, 50, 200)
zs = 1e-6 * np.linspace(-50, 50, 200)
x_tc, z_tc = np.meshgrid(xs, zs)  # 2D grid for interpolation

plt.scatter(x_tc, z_tc, c=rf_upper_right_interp((x_tc, z_tc)), s=0.2)
plt.colorbar()
plt.clim(0, 15000)
plt.show()


# %% Trap depth

# constants
q = scipy.elementary_charge
eps_o = scipy.epsilon_0
mass_be_kg = 9 * 1.67262192e-27  # kg
wrf = 2*np.pi * 230e6
vrf = 195
j = 1.602176634e-19

# Potential near trap center
xs = 1e-6 * np.linspace(-20, 20, 400)
# zs = np.zeros(len(xs))
zs = 1e-6 * np.linspace(-20, 20, 400)
zx_tc_coords = (xs, zs)

# rf_all_tc = rf_upper_right_interp(zx_tc_coords) + rf_lower_left_interp(zx_tc_coords) + rf_upper_left_interp(zx_tc_coords) + rf_lower_right_interp(zx_tc_coords)
rf_all_tc = CloughTocher2DInterpolator(zx_coords, data[:,2])(zx_tc_coords)

# Convert electric potential to energy potential (rf pseudopotential)
# rf_all_tc_epgrad = np.gradient(rf_all_tc) * 1000**2  # convert mm to m for gradient
# uzx = q * np.abs(rf_all_tc_epgrad)**2 * vrf**2 / (4 * mass_be_kg * wrf**2)  # eV units. Needs extra q for Joules
# Convert magnitude of electric field to energy potential (rf pseudopotential)
uzx = q * rf_all_tc**2 * vrf**2 / (4 * mass_be_kg * wrf**2)

plt.plot(xs, uzx, color='blue',label = 'Uzx')
# plt.plot(xs, uzx_v2, color='blue',label = 'Uzx')
plt.xlabel('x (mm)')
plt.ylabel('Potential (eV)')
plt.legend()
plt.show()

trap_depth = np.max(uzx)-np.min(uzx)
print("trap depth: " + str(np.round(trap_depth,4))+" eV")

# %% Fit potential

def pot_poly(xs, a, b, c):
    return a + b * xs + c * xs**2

# def pot_poly(xs, a, b, c):
#     return a + b * xs + c * xs**2

guess = [0, 10, 10]
popt, pcov = curve_fit(pot_poly, xs, uzx, p0=guess)
print('Fit parameters', popt)
print('fit uncertaints', np.sqrt(np.diag(pcov)))
fit = pot_poly(xs, *popt)
print('Secular frequency', np.sqrt(2 * popt[2] * q / mass_be_kg)/2/np.pi/1e6)  # * q to convert eV back to Joules and get units right for frequency

plt.plot(xs, uzx, color='red',label = 'Uzx')
plt.plot(xs, fit, '--k',label = 'fit')
plt.xlabel('x (m)')
plt.ylabel('Potential (eV)')
plt.legend()
plt.show()

# %%


# This is an updated script to process electrostatic data from COMSOL. 
# It takes COMSOL data and calculates the electrostatic potentials and secular frequencies.
# Supports an arbitraty number of DC electrodes (and one RF)

# Ensure working directory is same as file location
#script_directory = os.path.dirname(__file__)
#data_folder = os.path.join(script_directory, "data")
# os.chdir(r'G:\My Drive\Research\Projects\1D Trap prototyping\mono trap flat rf')

# Class to handle data loading/calculations, inherited by both electrode classes
class DataHandler:

    # Function to load and return data from file
    def _load_data(self, file_name, skiprows=8):
        try:
            data1 = np.loadtxt(file_name, skiprows=skiprows)

            # Unravel data
            x = np.array(data1[:,0])
            y = np.array(data1[:,1])
            z = np.array(data1[:,2])
            f = np.array(data1[:,3])

            # Format data
            data2 = [[x[i],y[i],z[i],f[i]] for i in range(len(x))]

            # Delete constant axis
            summed = np.sum(data2,axis=0)
            zero_axis = np.where(summed==0.0)
            data_new = np.delete(data2,zero_axis,axis=1)

            return data_new
        
        except FileNotFoundError:
            print(f"File unable to be located at {file_name}")
        except Exception as e:
            print(f"Error loading file {file_name}... exception throw: {e}")
            
            
    def _interpolator(self, data_in):
        # data_in.T gives [x, y, f]
        points = data_in[:, :2] # x1, x2
        values = data_in[:, 2]  # f
        
        # This step is the "heavy lifting" (Triangulation)
        interp_object = CloughTocher2DInterpolator(points, values)
        return interp_object
            
       
    # Function to calculate the potential at a given point
    # Passed X, Y position of point in question, and the data for corresponding plane     
    def _V_calc(self, q1, q2, interp_object):

        """
        q1: 1D array of x-coordinates
        q2: 1D array of y-coordinates
        """
        # Stack the 1D arrays into an (N, 2) array
        # e.g., if q1=[1, 2] and q2=[3, 4], qs becomes [[1, 3], [2, 4]]
        qs = np.column_stack((q1, q2))
        
        # Evaluate the interpolator
        vals = interp_object(qs)
        
        return vals
            
        
### Class for DC electrodes ###
class DCElectrode(DataHandler):
    # Load and store data 
    def __init__(self, electrode_number):
        self.electrode_number = electrode_number
        
        #edit here 

        # Construct file names using electrode number
        xy_file_name = comsol_data_path("DC" + str(electrode_number) + "_XY.txt")
        yz_file_name = comsol_data_path("DC" + str(electrode_number) + "_YZ.txt")
        zx_file_name = comsol_data_path("DC" + str(electrode_number) + "_XZ.txt")
        
        # Load data from each file above
        self.xy_data = self._load_data(xy_file_name)
        self.yz_data = self._load_data(yz_file_name)
        self.zx_data = self._load_data(zx_file_name)        
        
        self.xy_interp = self._interpolator(self.xy_data)
        self.yz_interp = self._interpolator(self.yz_data)
        self.zx_interp = self._interpolator(self.zx_data)     
        
    # Voltage functions
    def xyf(self, x, y):
        return self._V_calc(x, y, self.xy_interp)
    
    def yzf(self, x, y):
        return self._V_calc(x, y, self.yz_interp)
    
    def zxf(self, x, y):
        return self._V_calc(x, y, self.zx_interp)
    
### Class for RF Electrodes ###
class RFElectrode(DataHandler):
    
    # Vrf is the voltage on the rf electrode (V)
    # filenames_dict is a dictionary for data in three planes xy, yz, and zx
    def __init__(self, Vrf):
        self.Vrf = Vrf
        
        ### RF Constants ###
        self.q = scipy.elementary_charge
        self.eps_o = scipy.epsilon_0
        self.M_Yb = 171*1.67262192e-27
        self.d =  1000 #mm/m distance from
        self.frf = 29.6e6 #29.35*10**6
        self.wrf = 2*np.pi*self.frf
        ###########################
        
        # Old'
        xy_file_name = comsol_data_path("RF_XY.txt")
        yz_file_name = comsol_data_path("RF_YZ.txt")
        zx_file_name = comsol_data_path("RF_XZ.txt")        
        
        # New
        # folder = 'wheel trap/v0/'
        # xy_file_name = folder + "xy_plane"
        # yz_file_name = folder + "yz_plane"
        # zx_file_name = folder + "xz_plane"
        

        # Load data from each file above
        self.xy_data = self._load_data(xy_file_name)
        self.yz_data = self._load_data(yz_file_name)
        self.zx_data = self._load_data(zx_file_name) 
        
        # Load data from each file above
        self.xy_interp = self._interpolator(self.xy_data)
        self.yz_interp = self._interpolator(self.yz_data)
        self.zx_interp = self._interpolator(self.zx_data) 
        
    # Voltage Functions
    def xyf(self, x ,y):
        return self._V_calc(x, y, self.xy_interp)
    
    def yzf(self, y, z):
        return self._V_calc(y, z, self.yz_interp)
    
    def zxf(self, x, z):
        return self._V_calc(x, z, self.zx_interp)
    
    # Transform the imported RF data to the rf psuedopotential
    def Vrf_xy(self, x, y):
        return (self.q) * (self.xyf(x,y)**2) * (self.Vrf**2) / (4 * self.M_Yb * (self.wrf**2))
    
    def Vrf_yz(self, y, z):
        return (self.q) * (self.yzf(y,z)**2) * (self.Vrf**2) / (4 * self.M_Yb * (self.wrf**2))
    
    def Vrf_zx(self, x, z):
        return (self.q) * (self.zxf(x,z)**2) * (self.Vrf**2) / (4 * self.M_Yb * (self.wrf**2))
        
    
# A class to create/manage/use the Electrode classes above, allowing for total potential calculations
class ElectrodeStack:
    
    def __init__(self, num_dc_electrodes, Vdc, Vrf):
        self.num_dc_electrodes = num_dc_electrodes
        self.Vdc = Vdc
        self.Vrf = Vrf
        
        # Iteratively create the electrodes, storing them in a list for access
        self.dc_electrodes = []
        for i in range(num_dc_electrodes):
            electrode_number = i + 1
            electrode = DCElectrode(electrode_number)
            self.dc_electrodes.append(electrode)
            
        # Crete RF electrode
        self.rf_electrode = RFElectrode(Vrf)
            
    # Function to retrieve a specific electrode for direct access to the Electrode class methods
    def get_dc_electrode(self, electrode_number):
        index = electrode_number - 1
        try:
            return self.dc_electrodes[index]
        except:
            print(f"Electrode number {index} out of range; select a different electrode.")
            
    def get_rf_electrode(self):
        return self.rf_electrode
            
    # DC potentials
    def DCxy(self, x, y):
        total = 0
        # Iterate through each n electrode, adding its contribution to total DC potential
        for i in range(self.num_dc_electrodes):
            # Electrode n DC Voltage * electrode_n.xyf()
            dc_n = self.Vdc[i]
            dc_n_xyf = self.dc_electrodes[i].xyf(x, y)
            # Add contribution
            total += dc_n * dc_n_xyf
            
        return total
    
    def DCyz(self, x ,y):
        total = 0
        for i in range(self.num_dc_electrodes):
            dc_n = self.Vdc[i]
            dc_n_yzf = self.dc_electrodes[i].yzf(x, y)
            total += dc_n * dc_n_yzf
            
        return total
    
    def DCzx(self, x, y):
        total = 0
        for i in range(self.num_dc_electrodes):
            dc_n = self.Vdc[i]
            dc_n_zxf = self.dc_electrodes[i].zxf(x, y)
            total += dc_n * dc_n_zxf
        
        return total
    
    ### Total Potentials ###
    def Uxy(self, x, y):
        return self.DCxy(x, y) + self.rf_electrode.Vrf_xy(x, y)
    
    def Uyz(self, y, z):
        return self.DCyz(y, z) + self.rf_electrode.Vrf_yz(y, z)
    
    def Uzx(self, x, z):
        return self.DCzx(x, z) + self.rf_electrode.Vrf_zx(x, z)
          

# %%

### Variables to adjust ###
num_dc_electrodes = 3
Vrf = 1
#Vdc= [20.23390575, 12.55475617, 16.15436475] #endcaps, second middle, center electrode voltages
# frf can be adjusted within RFElectrode __init__ function
Vdc = [5.0,0.0,0.0]
# Vdc = [0]

# Create the electrodes and extract them
stack = ElectrodeStack(num_dc_electrodes, Vdc, Vrf)
rf1 = stack.get_rf_electrode()

# Unpack the list of DC electrodes for direct access (to use dc1.xyf(0, 0) for example)
# Uncomment only the number of electrodes that you are creating
dc1 = stack.get_dc_electrode(1)

# %%

### Example uses of methods ###

# ### DC Electrode methods (DC1xyf(x,y) in old code)
# You can address specific electrodes (dc1, dc2 etc)
print(dc1.xyf(0, 0)) 
# print(dc3.yzf(0.05, 0))
# print(dc2.zxf(0, 0.1))

# ### RF Methods (RFxyf(x, y) in old code) 
# print(rf1.xyf(0, 0)) 
# print(rf1.yzf(0, 0))
# print(rf1.zxf(0, 0))

# ### RF Pseudopotential (Vrf_xy(x,y) in old code)
# print(rf1.Vrf_xy(0, 0))
# print(rf1.Vrf_yz(0, 0))
# print(rf1.Vrf_zx(0, 0))

# ### Total DC (DCxy(x,y) in old code)
# print(stack.DCxy(0, 0)) 
# print(stack.DCyz(0, 0))
# print(stack.DCzx(0, 0))

# ### Total Potentials (Uxy(x,y) in old code)
# print(stack.Uxy(0, 0)) 
# print(stack.Uyz(0, 0))
# print(stack.Uzx(0, 0))

################################################################################################
#%%

#constants
q = scipy.elementary_charge
eps_o = scipy.epsilon_0
M_Be = 9 * 1.67262192e-27
m = 9 * 1.67262192e-27
d =  1000 #mm/m distance from
#frf = 38.6e6
#wrf = 2*np.pi*frf

#constants
q = scipy.elementary_charge
eps_o = scipy.epsilon_0
M_Yb = 171*1.67262192e-27
m = 171*1.67262192e-27
d =  1000 #mm/m distance from
#frf = 38.6e6
#wrf = 2*np.pi*frf

#%%

#coordiante ranges
xCtr = 0.
xRange = .5
yCtr = 0.
yRange = 0.06
zCtr = 0.
zRange = 0.06;
xMin = xCtr - xRange/2
xMax = xCtr + xRange/2
yMin = yCtr - yRange/2
yMax = yCtr + yRange/2
zMin = zCtr - zRange/2
zMax = zCtr + zRange/2


#%% Axial Trapping along x

n_vals = 1000
xvals = np.linspace(xMin,xMax,n_vals)
yvals = np.ones(n_vals)*yCtr
zvals = np.ones(n_vals)*zCtr


plt.plot(xvals,stack.Uxy(xvals,yvals),color='blue',label = 'Uxy',alpha = .3)
plt.plot(xvals,stack.Uzx(xvals,zvals),color='red',label = 'Uzx',alpha = .3)
plt.xlabel('x (mm)')
plt.ylabel('Potential (eV)')
plt.legend()
plt.show()


fxy = stack.Uxy(xvals,yvals)

trap_depth = np.max(fxy)-np.min(fxy)
print("trap depth: " + str(np.round(trap_depth,4))+" eV")


#%% title Minimum Position in x

# Create the 1D interpolating function
Uxy_1D_inter_x = interpolate.interp1d(xvals, fxy, kind='cubic', fill_value='extrapolate')

def Uxy_1D_inter_fun_x(x):
  return Uxy_1D_inter_x(x)

init_guess_x = 1e-10
result_x = minimize(Uxy_1D_inter_fun_x, init_guess_x, method='Nelder-Mead')
print("Minimum value found (eV):", np.round(result_x.fun,4))
print("At the point (um):", np.round((result_x.x-xCtr)*1000,10))

#%% Axial trapping along x-axis close to center

#create new y and z vals
yvals = np.ones(n_vals)*(yCtr+yRange/10)
zvals = np.ones(n_vals)*zCtr


plt.plot(xvals,stack.Uxy(xvals,yvals),color='blue',label = 'Uxy',alpha = .3)
plt.plot(xvals,stack.Uzx(xvals,zvals),color='red',label = 'Uzx',alpha = .3)
plt.xlabel('x (mm)')
plt.ylabel('Potential (eV)')
plt.title("Axial potential near center of trap")
plt.legend()
plt.show()

#%%  Radial trapping potential along y-axis
xvals = np.ones(n_vals)*xCtr
yvals = np.linspace(yMin,yMax,n_vals)
zvals = np.ones(n_vals)*zCtr

DC_xy = stack.DCxy(xvals,yvals)
RF_xy = rf1.Vrf_xy(xvals,yvals)
Uxy_vals = stack.Uxy(xvals,yvals)


plt.plot(yvals,DC_xy,color='blue',label = 'DC',alpha = .3)
plt.plot(yvals,RF_xy,color='red',label = 'RF',alpha = .3)
plt.plot(yvals,Uxy_vals,color='green',label = 'DC + RF',alpha = .3)
plt.xlabel('y (mm)')
plt.ylabel('Potential (eV)')
plt.legend()
plt.show()

trap_depth = np.max(DC_xy)-np.min(DC_xy)
print("trap depth: " + str(np.round(trap_depth,4))+" eV")

# @title Mininum trapping position in y

# Create the 1D interpolating function
Uxy_1D_inter_y = interpolate.interp1d(yvals, Uxy_vals, kind='cubic', fill_value='extrapolate')

#create functional input for the 1D interpolated function
def Uxy_1D_inter_fun_y(y):
  return Uxy_1D_inter_y(y)

init_guess_y = 1e-10
result_y = minimize(Uxy_1D_inter_fun_y, init_guess_y, method='Nelder-Mead')
print("Minimum value found (eV):", np.round(result_y.fun,4))
print("At the point (um):", np.round((result_y.x-yCtr)*1000,10))



#%% Radial Trapping along z-axis

n_vals = 100
xvals = np.ones(n_vals)*xCtr
yvals = np.ones(n_vals)*yCtr
zvals = np.linspace(zMin,zMax,n_vals)

DCzy_vals = stack.DCyz(yvals,zvals)
RFzy_vals = rf1.Vrf_yz(yvals,zvals)
Uzy_vals = stack.Uyz(yvals,zvals)


plt.plot(zvals,DCzy_vals,color='blue',label = 'DC',alpha = .3)
plt.plot(zvals,RFzy_vals,color='red',label = 'RF',alpha = .3)
plt.plot(zvals,Uzy_vals,color='green',label = 'DC + RF',alpha = .3)
plt.xlabel('z (mm)')
plt.ylabel('Potential (eV)')
plt.legend()
plt.show()


# Create the 1D interpolating function
Uzy_1D_inter_z = interpolate.interp1d(zvals, Uzy_vals, kind='cubic', fill_value='extrapolate')

#create functional input for the 1D interpolated function
def Uzy_1D_inter_fun_z(z):
  return Uzy_1D_inter_z(z)

init_guess_z = 1e-10
result_z = minimize(Uzy_1D_inter_fun_z, init_guess_z, method='Nelder-Mead')
print("Minimum value found (eV):", np.round(result_z.fun,4))
print("At the point (um):", np.round((result_z.x-zCtr)*1000,10))





#%% 2D plots
nvals = 500
x = np.linspace(xMin, xMax, nvals)
y = np.linspace(yMin, yMax, nvals)
z = np.linspace(zMin, zMax, nvals)

#%% 2D RF 


X1, Y1 = np.meshgrid(x,y)
Y2, Z2 = np.meshgrid(y, z)



X1_flat = X1.ravel()
Y1_flat = Y1.ravel()

Y2_flat = Y2.ravel()
Z2_flat = Z2.ravel()


Vrfxy_flat = rf1.Vrf_xy(X1_flat, Y1_flat)
Vrfxy = Vrfxy_flat.reshape(X1.shape)

Vrfzy_flat = rf1.Vrf_yz(Y2_flat,Z2_flat)
Vrfzy = Vrfzy_flat.reshape(Y2.shape)


Vrfxy = rotate(Vrfxy, 90,reshape=True)
Vrfzy = rotate(Vrfzy, 90,reshape=True)

fig, axs = plt.subplots(1, 2, figsize=(18, 6))

cont1 =  axs[0].contourf(X1,Y1,Vrfxy, levels = 20,cmap = 'hsv')
cont2 =  axs[1].contourf(Z2,Y2,Vrfzy, levels = 20,cmap = 'hsv')


axs[0].set_xlabel('X (mm)')
axs[0].set_ylabel('Y (mm)')
axs[0].set_title('RF pseudopotential in XY plane')

axs[1].set_xlabel('Z (mm)')
axs[1].set_ylabel('Y (mm)')
axs[1].set_title('RF pseudopotential in YZ plane')

fig.colorbar(cont1, ax=axs[0])
fig.colorbar(cont2, ax=axs[1])

plt.show()



#%% 2D DC Potential



X1, Y1 = np.meshgrid(x,y)
Y2, Z2 = np.meshgrid(y, z)

X1_flat = X1.ravel()
Y1_flat = Y1.ravel()

Y2_flat = Y2.ravel()
Z2_flat = Z2.ravel()


dcxy_flat = stack.DCxy(X1_flat,Y1_flat)
dczy_flat = stack.DCyz(Y2_flat,Z2_flat)

dcxy = dcxy_flat.reshape(X1.shape)
dczy = dczy_flat.reshape(Y1.shape)


dcxy = rotate(dcxy, 90,reshape=True)
dczy = rotate(dczy, 90,reshape=True)


fig, axs = plt.subplots(1, 2, figsize=(18, 6))

cont1 =  axs[0].contourf(X1,Y1,dcxy, levels = 50,cmap = 'hsv')
cont2 =  axs[1].contourf(Y2,Z2,dczy, levels = 50,cmap = 'hsv')

axs[0].set_ylabel('Y (mm)')
axs[0].set_xlabel('X (mm)')
axs[0].set_title('DC potential in XY plane')

axs[1].set_xlabel('Y (mm)')
axs[1].set_ylabel('Z (mm)')
axs[1].set_title('DC potential in YZ plane')

fig.colorbar(cont1, ax=axs[0])
fig.colorbar(cont2, ax=axs[1])

plt.show()

#%% 2D Total Potential

X1, Y1 = np.meshgrid(x,y)
Y2, Z1 = np.meshgrid(y,z)


X1_flat = X1.ravel()
Y1_flat = Y1.ravel()

Y2_flat = Y2.ravel()
Z2_flat = Z2.ravel()


uxy_flat = stack.Uxy(X1_flat,Y1_flat)
uzy_flat = stack.Uyz(Y2_flat,Z2_flat)

uxy = uxy_flat.reshape(X1.shape)
uzy = uzy_flat.reshape(Y2.shape)

uxy = rotate(uxy, 90,reshape=True)
uzy = rotate(uzy, 90,reshape=True)



fig, axs = plt.subplots(1, 2, figsize=(18, 6))
cont1 =  axs[0].contourf(X1,Y1,uxy, levels = 50,cmap = 'hsv')
cont2 =  axs[1].contourf(Z2,Y2,uzy, levels = 50,cmap = 'hsv')

axs[0].set_ylabel('Y (mm)')
axs[0].set_xlabel('X (mm)')
axs[0].set_title('Total potential in XY plane')

axs[1].set_xlabel('Z (mm)')
axs[1].set_ylabel('Y (mm)')
axs[1].set_title('Total potential in YZ plane')

fig.colorbar(cont1, ax=axs[0])
fig.colorbar(cont2, ax=axs[1])

plt.show()

#%% Principal axes and secular frequencies- from a fit to 2d quadrupoles


# Uzy fits: $U_{zy}(y,z)=Ay^{2}+Byz+Cz^{2}+Dy+Ez+F$

def Uzy_fits(coords,A,B,C,D,E,F):
  y,z = coords
  fun = A*y**2 + B*y*z + C*z**2 + D*y + E*z + F
  return fun

num_points = 100
nvals_y = (yMax - yMin)/100
nvals_z = (zMax - zMin)/100

#create mesh
Y = np.arange(yMin,yMax,nvals_y)
Z = np.arange(zMin,zMax,nvals_z)

Y, Z = np.meshgrid(Y,Z)

Y_flat = Y.ravel()
Z_flat = Z.ravel()


uzy_flat = stack.Uyz(Y_flat, Z_flat)
uzy = uzy_flat.reshape(Y.shape)
uzy = rotate(uzy,90,reshape=True)


coords_zy = np.vstack((Y_flat,Z_flat)) #format data vertically (y,z)
fits_zy, other_stuff_zy = curve_fit(Uzy_fits,coords_zy, uzy_flat)


Uzy_fitted = Uzy_fits(coords_zy,*fits_zy)
Uzy_fitted = Uzy_fitted.reshape(Y.shape) #reshape according to Y data



# @title Minimum yz values
def Uzy_secular(coords):
  val = Uzy_fits(coords,*fits_zy)
  return val

init_guess_zy = [1e-6,1e-6]

result_zy = minimize(Uzy_secular, init_guess_zy, method='L-BFGS-B')
y_min = result_zy.x[0]
z_min = result_zy.x[1]

min_yz = [y_min,z_min]
# print("Minimum value found (eV):", np.round(result_zy.fun,4))
# print("At the point (um):", (np.round(y_min,10),np.round(z_min,10)))

# @title Uxy fits: $U_{xy}(x,y)=Ax^{2}+Bxy+Cy^{2}+Dx+Ey+F$
#define function for fitting
def Uxy_fits(coords,A,B,C,D,E,F):
  x,y = coords
  fun = A*x**2 + B*x*y + C*y**2 + D*x + E*y + F
  return fun

num_points = 1000
nvals_x = (xMax - xMin)/100
nvals_y = (yMax - yMin)/100

#create mesh
X = np.arange(xMin,xMax,nvals_x)
Y = np.arange(yMin,yMax,nvals_y)
X,Y = np.meshgrid(X,Y)

X_flat = X.ravel()
Y_flat = Y.ravel()

uxy_flat = stack.Uxy(X_flat,Y_flat) #functional data
uxy = uxy_flat.reshape(X.shape)
uxy = rotate(uxy,90,reshape=True)


coords_xy = np.vstack((X_flat,Y_flat)) #format data vertically (x,y)

guesses = [0,0,0,0,0,0]

fits_xy, other_stuff_xy = curve_fit(Uxy_fits,coords_xy, uxy_flat)

Uxy_fitted = Uxy_fits(coords_xy,*fits_xy)
Uxy_fitted = Uxy_fitted.reshape(X.shape) 


#reshape according to X data
# print(fits_xy)

# plt.contourf(X,Y,uxy,levels = 20,cmap = 'hsv',alpha = 0.3)
# plt.contour(X,Y,uxy,levels = 20,colors='black',alpha=.7)

# plt.contourf(X,Y,Uxy_fitted,levels=20,cmap = 'hsv',alpha = .3)
# plt.contour(X,Y,Uxy_fitted,levels=20,colors='blue',alpha = .7)
# plt.colorbar()
# plt.xlabel('X (mm)')
# plt.ylabel('Y (mm)')
# plt.title('Total potential in xy plane')
# plt.show()

# @title Minimum xy values
def Uxy_secular(coords):
  val = Uxy_fits(coords,*fits_xy)
  return val

init_guess_xy = [1e-6,1e-6]

result_xy = minimize(Uxy_secular, init_guess_xy, method='L-BFGS-B')

x_min = result_xy.x[0]
y_min = result_xy.x[1]

min_xy = [x_min,y_min]
# print("Minimum value found (eV):", np.round(result_xy.fun,4))
# print("At the point (um):", (np.round(x_min,10),np.round(y_min,10)))


# For a function of the form:
# 
# $f(x,y)=ax^{2}+by^{2}+c*xy+d*x+e*y+f$, \
# the rotation angle will be
# 
# $\theta = \frac{1}{2}Arctan(\frac{c}{b-a})$

# @title Compute angle of ellipse relative to original axes
def theta(fits):
  a,b,c,d,e,f = fits
  theta = 0.5*np.arctan((b)/(a-c))
  return theta


theta_x = np.round(theta(fits_xy),10)
theta_y = -(np.round(theta(fits_zy),5))
theta_z = theta_y + np.pi /2

# print(theta_x,theta_y,theta_z)

# @title Compute axes of ellipse
def cos(theta):
  return np.cos(theta)

def sin(theta):
  return np.sin(theta)

def y_axes(y_min,z_min,amp,theta_y,theta_z):

  y_prime = y_min + amp*cos(theta_y)
  z_prime = z_min + amp*sin(theta_y)
  coords = np.array([y_prime,z_prime])
  return coords.T


def z_axes(y_min,z_min,amp,theta_y,theta_z):

  y_prime = y_min + amp*cos(theta_z)
  z_prime = z_min + amp*sin(theta_z)
  coords = np.array([y_prime,z_prime])
  return coords.T

amp_y = np.arange(yMin,yMax,.001)
amp_z = np.arange(zMin,zMax,.001)

prin_z_axes = z_axes(y_min,z_min,amp_z,theta_y,theta_z)
prin_y_axes = y_axes(y_min,z_min,amp_y,theta_y,theta_z)


fig, axs = plt.subplots(1, 1)

nvals = 500
Y2 = np.linspace(yMin,yMax,nvals)
Z2 = np.linspace(zMin,zMax,nvals)
Y2,Z2 = np.meshgrid(Y2,Z2)

Y2_flat = Y2.ravel()
Z2_flat = Z2.ravel()

uzy_flat = stack.Uyz(Y2_flat,Z2_flat)
uzy = uzy_flat.reshape(Y2.shape)

cont2 =  axs.contourf(Z2,Y2,uzy, levels = 50,cmap = 'hsv')

axs.set_xlabel('Z (mm)')
axs.set_ylabel('Y (mm)')
axs.set_title('Total potential in YZ plane')

fig.colorbar(cont2, ax=axs)

plt.plot(prin_z_axes.T[0], prin_z_axes.T[1], label='prin z-axis')
plt.plot(prin_y_axes.T[0], prin_y_axes.T[1], label='prin y-axis')
plt.legend()
plt.show()


print('theta_y (degree): ',theta_y / np.pi * 180)
print('theta_z (degree): ',theta_z / np.pi * 180)


wy = (1/2/np.pi)*np.sqrt(1e6*scipy.e*2*(fits_zy[0]*cos(theta_y)**2+fits_zy[1]*sin(theta_y)*cos(theta_y)+fits_zy[2]*sin(theta_y)**2)/m)
wz = (1/2/np.pi)*np.sqrt(1e6*scipy.e*2*(fits_zy[0]*sin(theta_y)**2-fits_zy[1]*sin(theta_y)*cos(theta_y)+fits_zy[2]*cos(theta_y)**2)/m)
wx = (1/2/np.pi)*np.sqrt(1e6*scipy.e*2*(fits_xy[0]*cos(theta_x)**2-fits_xy[1]*sin(theta_x)*cos(theta_x)+fits_xy[2]*sin(theta_x)**2)/m)

print('pseudoharmonic apporximation Wx, Wy, Wz: (MHz)', wx/1e6, wy/1e6, wz/1e6)

#%% Axial polynomial fit 

nvals = 1000
xvals = np.linspace(xMin, xMax, nvals)
yvals = np.linspace(yMin, yMax, nvals)
zvals = np.linspace(zMin, zMax, nvals)

#get 1D data for polynomial fit 
Ux_vals = stack.Uxy(xvals,np.zeros(len(xvals)))  # Replace with your actual function call to get Uxy values
Uy_vals = stack.Uxy(np.zeros(len(xvals)),yvals)  # Replace with your actual function call to get Uxy values
Uz_vals = stack.Uyz(np.zeros(len(xvals)),zvals)  # Replace with your actual function call to get Uxy values


# Fit polynomial of degree 2 (quadratic)
x_coeffs = np.polyfit(xvals, Ux_vals, 6)  # The second argument here is the degree of the polynomial
y_coeffs = np.polyfit(yvals, Uy_vals, 2)  # The second argument here is the degree of the polynomial
z_coeffs = np.polyfit(zvals, Uz_vals, 2)  # The second argument here is the degree of the polynomial

print("x: "+str(x_coeffs))
print("y: "+str(y_coeffs))
print("z: "+str(z_coeffs))


Vx = np.polyval(x_coeffs, xvals)
Vy = np.polyval(y_coeffs, yvals)
Vz = np.polyval(z_coeffs, zvals)


plt.plot(xvals, Ux_vals, label="Original Data")
plt.plot(xvals, Vx, label="Polynomial Fit", linestyle='--')
plt.xlabel('x')
plt.ylabel('Vx (Potential)')
plt.legend()
plt.show()


plt.plot(yvals, Uy_vals, label="Original Data")
plt.plot(yvals, Vy, label="Polynomial Fit", linestyle='--')
plt.xlabel('y')
plt.ylabel('Vy (Potential)')
plt.legend()
plt.show()

plt.plot(zvals, Uz_vals, label="Original Data")
plt.plot(zvals, Vz, label="Polynomial Fit", linestyle='--')
plt.xlabel('z')
plt.ylabel('Vz (Potential)')
plt.legend()
plt.show()

#%%

# x_coeffs_rev = x_coeffs[::-1]

x = np.linspace(-0.25, 0.25, 100)
Vx = np.polyval(x_coeffs, x)

plt.plot(x, Vx)
plt.xlabel('x')
plt.ylabel('Potential V')
plt.show()


# y_coeffs_rev = y_coeffs[::-1]

y = np.linspace(-0.03, 0.03, 100)
Vy = np.polyval(y_coeffs, y)

plt.plot(y, Vy)
plt.xlabel('y')
plt.ylabel('Potential V')
plt.show()


# z_coeffs_rev = z_coeffs[::-1]

z = np.linspace(-0.03, 0.03, 100)
Vz = np.polyval(z_coeffs, z)

plt.plot(z, Vz)
plt.xlabel('z')
plt.ylabel('Potential V')
plt.show()




# %% # of ions / Electric potential function
x_coeffs_rev = x_coeffs[::-1]
y_coeffs_rev = y_coeffs[::-1]
z_coeffs_rev = z_coeffs[::-1]

#definitons
e = scipy.elementary_charge
eps_o = scipy.epsilon_0
m = 171*1.67262192e-27
delta_k = np.sqrt(2)*2*np.pi/(355e-9)
hbar = scipy.hbar

# lc = (e**2/(4*np.pi*eps_o*m*wz**2))**(1/3)
recoil = (hbar*(delta_k)**2 ) / (2*m)

# number of ions
N = 10

# @jit(nopython=True, fastmath=True)
def potential_energy(positions):
    # wx, wy, wz, N, m, e, epsilon_0 = params
    xs = positions[:N]
    ys = positions[N:2*N]
    zs = positions[2*N:3*N]
    
    # Initialize potential energy terms
    Vx = np.zeros_like(xs)
    Vy = np.zeros_like(ys)
    Vz = np.zeros_like(zs)
    
    # Calculate Vx, Vy, and Vz using a manual loop for summing
  
    for j in range(len(x_coeffs_rev)):
        Vx += x_coeffs_rev[j] * ((1000*xs)**j)
        
    for j in range(len(y_coeffs_rev)):
        Vy += y_coeffs_rev[j] * ((1000*ys)**j)
        
    for j in range(len(z_coeffs_rev)):
        Vz += z_coeffs_rev[j] * ((1000*zs)**j) 
    
    # Harmonic energy
    harm_energy = e * np.sum(Vx + Vy + Vz) 
    
    # electronic interaction
    interaction = 0
    for i in range(N):
        for j in range(N):
            if j != i:
                interaction += 1/np.sqrt((xs[i]-xs[j])**2 + (ys[i]-ys[j])**2 + (zs[i]-zs[j])**2)
    interaction = e**2/8/np.pi/eps_o * interaction
    
    # print(harm_energy+interaction)
    return harm_energy + interaction


xs_0 = np.linspace(-1,1,N) * 1e-5
ys_0 = np.linspace(-1,1,N) * 0
zs_0 = np.linspace(-1,1,N) * 0

pos = np.append(np.append(xs_0, ys_0), zs_0)

pot_en = potential_energy(pos)
print('Potential Energy', pot_en)

plt.plot(xs_0 * 1e6, ys_0 * 1e6, '.', color='royalblue', markersize=12, markeredgecolor='darkblue')
plt.xlabel('x distance (micron)')
plt.ylabel('y distance (micron)')
plt.title('Initial ion position guess')
plt.grid()
plt.show()

# %% Minimize potential energy to determine ion crystal positions
bounds = [(xMin*1e-3, xMax*1e-3)] * N + [(yMin*1e-3, yMax*1e-3)] * N + [(zMin*1e-3, zMax*1e-3)] * N  # bounds for N ions in x, y, z

# run bad guess through optimization with on a few iterations
pos_better = minimize(potential_energy, pos, method='COBYLA', bounds=bounds, options={'tol':1e-30, 'maxiter':2000})

# Get fine results with better initial best and many iterations
res = minimize(potential_energy, pos_better.x, method='COBYLA', bounds=bounds, options={'tol':1e-30, 'maxiter':80000})

# %% Plotting equilibrium positions and uniformity
# Plot ion positions

xs_f = res.x[:N]
ys_f = res.x[N:2*N]
zs_f = res.x[2*N:3*N]


sorted_indices = np.argsort(xs_f)
zs_f = zs_f[sorted_indices]
xs_f = xs_f[sorted_indices]
ys_f = ys_f[sorted_indices]

fig, axes = plt.subplots(1,3,figsize=(15,5))

axes[0].plot(xs_f * 1e6, ys_f * 1e6, '.', markersize=16, color='royalblue', markeredgecolor='k')
axes[0].set_title('Ion equilibrium position')
axes[0].set_xlabel('x distance (um)')
axes[0].set_ylabel('y distance (um)')
axes[0].set_ylim(-100, 100)
axes[0].set_xlim(-100, 100)

# axes[0].set_ylim(-5, 5)
# axes[0].set_xlim(-10, 10)
axes[0].grid()

# Add index labels for the first plot
# for i in range(len(xs_f)):
#     axes[0].text(xs_f[i] * 1e6+10, ys_f[i] * 1e6+10, f'{i}', color='black', fontsize=10, ha='left', va='top')

axes[1].plot(zs_f * 1e6, ys_f * 1e6, '.', markersize=16, color='royalblue', markeredgecolor='k')
axes[1].set_title('Ion equilibrium position')
axes[1].set_xlabel('z distance (um)')
axes[1].set_ylabel('y distance (um)')
axes[1].set_ylim(-100, 100)
axes[1].set_xlim(-100, 100)

# axes[1].set_ylim(-5, 5)
# axes[1].set_xlim(-10, 10)

axes[1].grid()

# Add index labels for the second plot
# for i in range(len(zs_f)):
#     axes[1].text(zs_f[i] * 1e6+10, ys_f[i] * 1e6+10, f'{i}', color='black', fontsize=10, ha='left', va='top')
#     axes[1].text(zs_f[i], ys_f[i], f'{i}', color='black', fontsize=10, ha='left', va='top')


axes[2].plot(xs_f * 1e6, zs_f * 1e6, '.', markersize=16, color='royalblue', markeredgecolor='k')
axes[2].set_title('Ion equilibrium position')
axes[2].set_xlabel('x distance (mm)')
axes[2].set_ylabel('z distance (mm)')
axes[2].set_ylim(-100, 100)
axes[2].set_xlim(-100, 100)

# axes[2].set_ylim(-20, 20)
# axes[2].set_xlim(-20, 20)

axes[2].grid()

# Add index labels for the third plot
# for i in range(len(xs_f)):
#     axes[2].text(xs_f[i] * 1e6+10, zs_f[i] * 1e6+10, f'{i}', color='black', fontsize=10, ha='left', va='top')

plt.tight_layout()
plt.show()

