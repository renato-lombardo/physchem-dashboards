import numpy as np

def hill(L: float, L50: float, n: float):
    '''
    Compute saturation of protein using Hill-Langmuir equation
    
    Parameters
    ----------
    L : float or array
        ligand concentration (pO2 in the case of hemoglobin)
    L50 : float
        ligand concentration that correspond to a saturation of 0.5.
        (p50 in the case of hemoglobin)
    n : 
        Hill coefficient. It usually corresponds to the number of bing sites
        (4 in the case of hemoglobin)
    
    Return
    ------
    s : float or array
        protein saturation
    '''
    Kd = L50**n # dissociation constant
    s = (L**n)/(Kd+L**n) # Hill-Langmuir equation
    return s