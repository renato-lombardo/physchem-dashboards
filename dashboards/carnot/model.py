import numpy as np


R = 8.31

def w_iso_T(Vi, Vf, T):
    '''
    compute work in a reversible isothermal expansion
    
    Parameters
    ----------
    Vi : float
        initial volume
    V2 : float
        final volume
    T : float 
        temperature (absolute)
        
    Returns
    -------
    float
        work
    '''
    return -R*T*np.log(Vf/Vi)

def w_adiab(Ti, Tf, Cv):
    '''
    compute work in an adiabatic expansion
    
    Parameters
    ----------
    Ti : float
        initial temperature
    Tf : float
        final temperature
    Cv : float 
        heat capacity at constant volume
        
    Returns
    -------
    float
        work
    '''
    
    return Cv*(Tf-Ti)

def iso_T(Vi, Vf, T, n=100):
    V = np.linspace(Vi, Vf, n)
    p = R*T/V
    return V, p

def adiab(pi, Vi, Vf, gamma, n=100):
    V = np.linspace(Vi, Vf, n)
    p = (pi*Vi**gamma)/(V**gamma)
    return V, p


def carnot(T_c, T_h, V1, V2, Cv = 1.5*R, Cp=2.5*R):
    '''
    Compute Carnot cycle parameters
    
    Parameters
    ----------
    T_c : float
        cold temperature
    T_h : float
        hot temperature
    V1 : float
        volume at the beginning of isothermal expansion
    V2 : float
        volume the end of isothermal expansion
    Cv : float
        heat capacity at costant volume
    Cp : float
        heat capacity at costant pressure
        
    Returns
    -------
    states : dict
        dictionary of state parameters: V, p, T for eact state
    t : dict
        dictonary of parameters for each transformation
    '''
    
    gamma = Cp/Cv
    g = gamma # for notation convenience
    g_1 = gamma-1 # for notation convenience
    
    # Define states
    s = [{}, {}, {}, {}]
    
    s[0]['T'] = T_h # Th
    s[0]['V'] = V1  # V1
    s[0]['p'] = R*s[0]['T']/s[0]['V'] # p1
    
    s[1]['T'] = T_h # Th
    s[1]['V'] = V2 # v2
    s[1]['p'] = R*T_h/V2# p2
    
    s[2]['T'] = T_c # Tc
    s[2]['V'] = (s[1]['T']/s[2]['T'])**(1/g_1) * s[1]['V'] # V3
    s[2]['p'] = R*s[2]['T']/s[2]['V'] # p3
    
    s[3]['T'] = T_c # Tc
    s[3]['V'] = s[2]['V']*s[0]['V']/s[1]['V'] # V3/V4 = V2/V1
    s[3]['p'] = R*s[3]['T']/s[3]['V'] # p4
    
    t = [{}, {}, {}, {}] # transformations
    
    # isothermic expansion
    t[0]['V'], t[0]['p'] = iso_T(s[0]['V'], s[1]['V'], s[0]['T'])
    t[0]['DU'] = 0
    t[0]['w'] = w_iso_T(s[0]['V'], s[1]['V'], s[0]['T'])
    t[0]['q'] = -1 * t[0]['w']
    t[0]['DS'] = t[0]['q']/s[0]['T']
    
    # adiabatic expansion
    t[1]['V'], t[1]['p'] = adiab(s[1]['p'], s[1]['V'], s[2]['V'], gamma)
    t[1]['w'] = w_adiab(s[1]['T'], s[2]['T'], Cv)
    t[1]['DU'] = t[1]['w']
    t[1]['q'] = 0
    t[1]['DS'] = 0
    
    # isothermic compression
    t[2]['V'], t[2]['p'] = iso_T(s[2]['V'], s[3]['V'], s[2]['T'])
    t[2]['DU'] = 0
    t[2]['w'] = w_iso_T(s[2]['V'], s[3]['V'], s[2]['T'])
    t[2]['q'] = -1 * t[2]['w']
    t[2]['DS'] = t[2]['q']/s[2]['T']
    
    # adiabatic expansion
    t[3]['V'], t[3]['p'] = adiab(s[3]['p'], s[3]['V'], s[0]['V'], gamma)
    t[3]['w'] = w_adiab(s[3]['T'], s[0]['T'], Cv)
    t[3]['DU'] = t[3]['w']
    t[3]['q'] = 0
    t[3]['DS'] = 0
     
    eta = 1 - (T_c/T_h)
    w_tot = sum([t[i]['w'] for i in range(len(t))])
    
    return s, t, eta, w_tot