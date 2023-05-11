import numpy as np

def michaelis_menten(S, KM, k2, E0, I=0, KI=1, inhibition=''):
    '''
    Compute initial reacton rate v0 for an Enzyme using Michaelis-Menten kinetics
    taking into accout possible inhibition
    
    Parameters
    ----------
    S : float or array
        substarte concentration
    KM : float
        Michalelis-Menten constant
    k2 : float
        catalytic constant (turnover number)
     E0 : float
        enzyme concentration
     I : float
        inhibitor concentration
     KI : float
        inhibitor/enzyme complex degradation equilibrium constant
     inhibition : str
         type of inhibitor
         
    Return
    ------
    v0 : floar or array
        initial reaction rate
    KM : float
        Michalelis-Menten constant (effective)
    k2 : float
        catalytic constant (effective)
    '''
    inhibition = str(inhibition).lower()
    factor = (1 + I/KI)
    if inhibition == 'competitive':
        KM = KM * factor
    elif inhibition == 'noncompetitive':
        k2 = k2 / factor
    elif inhibition == 'uncompetitive':
        k2 =k2 / factor
        KM = KM / factor
    v0 = (k2 * E0 * S) / (KM + S)
    return v0, KM, k2