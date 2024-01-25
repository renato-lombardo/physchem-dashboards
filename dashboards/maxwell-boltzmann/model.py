import numpy as np



# dictionary with molecules information molecular masses in g mol^-1
molecules = {
    'H_2': {'M': 1.00784*2},
    'He': {'M': 4.002602},
    'N_2': {'M': 14.007*2},
    'O_2': {'M': 15.999*2},
    'F_2': {'M': 18.998*2},
    'Ne': {'M': 20.1797},
    'Cl_2': {'M': 35.453*2},
    'Ar': {'M': 39.948},
    'Kr': {'M': 83.80},
    'Xe': {'M': 131.29}
    }


#######################################################
# Define functions for Maxwell-Boltzmann distribution #
# and characteristic speeds                           #
#######################################################
def MB(v: np.ndarray, M: float, T: float):
    '''
    compute Maxwell Boltzmann distribution
    
    Parameters
    ----------
    v : numpy.ndarray
        speed range
    M : float
        molecular molar mass in g mol-1
    T : float
        temperature in K
    
    Returns
    ------
    fv : numpy.ndarray
        probabilty density
    '''
    R = 8.31 # J K^-1 mol^-1
    M = M/1000. # kg mol^-1
    N = np.sqrt((M/(2*np.pi*R*T))**3) # normalization factor
    return N*4*np.pi*v*v*np.exp(-((M*v*v))/(2*R*T)) # probability density

def v_p(M: float, T: float):
    '''
    compute most probable speed in Maxwell-Boltzmann distribution
    Parameters
    ----------
    M : float
        molecular molar mass in g mol-1
    T : float
        temperature in K
        
    Returns
    ------
    v_p : float
        most probable speed
    '''
    R = 8.31 # J K^-1 mol^-1
    M = M/1000. # kg mol^-1
    return np.sqrt(2*R*T/M)

def v_avg(M: float, T: float):
    '''
    compute average speed in Maxwell-Boltzmann distribution
    Parameters
    ----------
    M : float
        molecular molar mass in g mol-1
    T : float
        temperature in K
    
    Returns
    ------
    v_avg : float
        average speed
    '''
    R = 8.31 # J K^-1 mol^-1
    M = M/1000. # kg mol^-1
    return np.sqrt(8*R*T/(np.pi*M))

def v_rms(M: float, T: float): 
    '''
    compute root mean square speed in Maxwell-Boltzmann distribution
    
    Parameters
    ----------
    M : float
        molecular molar mass in g mol-1
    T : float
        temperature in K
    
    Returns
    ------
    v_rms : float
        root mean square speed
    '''
    R = 8.31 # J K^-1 mol^-1
    M = M/1000. # kg mol^-1
    return np.sqrt(3*R*T/M)
