import numpy as np

R = 8.31 # universal gas constant J/ K mol
def DG_mix(beta: float, T: float) -> (np.ndarray, np.ndarray):
    '''
    compute molar Gibbs energy of mixing
    '''
    # molar fraction of component 1
    x1 = np.linspace(0.0001, 1, 10000)
    x2 = 1.0001-x1
    DG = R*T*(x1*np.log(x1)+x2*np.log(x2))+beta*x1*x2
    return x1, DG

def DS_mix(T: float) -> (np.ndarray, np.ndarray):
    '''
    compute molar entropy of mixing
    '''
    # molar fraction of component 1
    x1 = np.linspace(0.0001, 1, 10000)
    x2 = 1.0001-x1
    DS = -R*(x1*np.log(x1)+x2*np.log(x2))
    return x1, DS

def DH_mix(beta: float, T: float) -> (np.ndarray, np.ndarray):
    '''
    compute molar hentalpy of mixing
    '''
    x1 = np.linspace(0.0001, 1, 10000)
    x2 = 1.0001-x1
    DH = beta*x1*x2
    return x1, DH
    