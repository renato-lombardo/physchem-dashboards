import numpy as np
import pint
import warnings


# initialize units registry
ureg = pint.UnitRegistry()

# Silence NEP 18 warning
# see Pint documentation
# https://pint.readthedocs.io/en/stable/numpy.html
with warnings.catch_warnings():
    warnings.simplefilter("ignore")

def boltzmann_factor(E, T):
    '''
    computes Boltzman factor
    
    Parameters
    ----------
    E : float or pint.Quantity
        energy level (joule by default)
    T : float or pint.Quantity
        Temperature (kelvin, by default)
        
    Returns
    -------
    bf : pint.Quantity
        Boltzman factor
    '''
    # use quantites with units
    if not isinstance(E, pint.Quantity):
        E *= ureg.eV
    if not isinstance(T, pint.Quantity):
        T *= ureg.kelvin
    k = ureg.boltzmann_constant
    bf = np.exp(-1*E/(k*T))
    return bf

def population(E, T):
    '''
    Computes population distribution of a set energy levels
    
    Parameters
    ----------
    E : np.array of float or pint.Quantity
        energy levels (joule by default)
    T : float or pint.Quantity
        Temperature (kelvin, by default)
        
    Returns
    -------
    pop : pint.Quantity
    '''
    levels = boltzmann_factor(E,T)
    # compute partition function
    Q = levels.sum()
    pop = levels/Q
    return pop