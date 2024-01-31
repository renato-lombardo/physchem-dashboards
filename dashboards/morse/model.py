import numpy as np
import pint
import warnings

# define needed physical constants
# we could use scipy for this, but there is no need to have such big dependency
# from scipy.constants import h, c, u

h = 6.62607015e-34 # the Planck constant
c = 299792458.0 # speed of light in vacuum
u = 1.6605390666e-27 # atomic mass constant (in kg)


# initialize units registry
ureg = pint.UnitRegistry()
Q_ = ureg.Quantity

# Silence NEP 18 warning
# see Pint documentation
# https://pint.readthedocs.io/en/stable/numpy.html
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    Q_([]) 

# Dictionary with scpectroscopic data for various diatomic molecules from
# Handbook of Chemistry and Physics 87th editions
# SPECTROSCOPIC CONSTANTS OF DIATOMIC MOLECULES 9-82
# we : wavenumber in cm-1; wexe : anharmonic parameter, in cm-1
# m1, m2 : masses of atom 1 and atom 2, in atomic mass unit
# re : equilibrium distance (bond length), in angstrom

molecules = {
              'H_2': {'we': 4401.21, 'wexe': 121.34, 'm1': 1, 'm2': 1, 're': 0.74144},
              'LiH': {'we': 1405.65, 'wexe': 23.20, 'm1': 7, 'm2': 1, 're': 1.59490},
              'KH':  {'we': 983.6, 'wexe': 14.3, 'm1': 39, 'm2': 1, 're': 2.243},
              'HCl': {'we': 2990.945, 'wexe': 52.818595, 'm1': 1, 'm2': 35, 're': 1.2745},
              'NaCl': {'we': 366, 'wexe': 2.05, 'm1': 23, 'm2': 35, 're': 2.36080},
              'F_2': {'we': 916.64, 'wexe': 11.24, 'm1': 29, 'm2': 29, 're': 1.41193},
              'Br_2': {'we': 325.32, 'wexe': 1.08, 'm1': 79, 'm2': 79, 're': 2.2811},
              'Cl_2': {'we': 559.7, 'wexe': 2.68, 'm1': 35, 'm2': 35, 're': 1.988},
              'I_2': {'we': 214.50, 'wexe': 0.61, 'm1': 127, 'm2': 127, 're': 2.666},
              'O_2': {'we': 1580.19, 'wexe': 11.98, 'm1': 16, 'm2': 16, 're': 1.20752},
              'N_2': {'we': 2358.57, 'wexe': 14.32, 'm1': 14, 'm2': 14, 're': 1.09769}
             }


def oscillator(mol, oscillator_type, **kwargs):
    ''' oscillator factory '''
    if oscillator_type.lower() in ('morse', 'anharmonic', 'realistic'):
        return Morse.from_spect_data(molecules[mol], **kwargs)
    elif oscillator_type.lower() in ('hooke', 'harmonic', 'ideal'):
        return Hooke.from_spect_data(molecules[mol], **kwargs)
    else:
        raise ValueError


class BaseOscillator:
    '''
    base class for oscillator potential computation
    '''
    def __init__(self, r=np.array([])):
        self.r = r # distance
        self.V = self.compute()
    
    def compute(self):
        raise NotImplementedError
        
    def _energy_levels(self):
        raise NotImplementedError
    
    def _compute_levels(self, n_lines=30):
        '''
        compute levels to plot in the graph
        '''
        lines = []
        r = self.r
        re = self.re
        V = self.V
        levels = self._energy_levels()
        # each line has an y value corresponding to the energy of the level
        # and x values that corresponds to the intercept between energy level
        # and the potential curve
        i_re = (np.abs(r-re)).argmin()
        for l in levels:
            idx1 = (np.abs(V[:i_re]-l)).argmin()
            idx2 = (np.abs(V[i_re:]-l)).argmin() + i_re
            lx = r[[idx1, idx2]]
            ly = np.array([l.magnitude]*2) * l.units
            lines.append((lx, ly))
        self.levels = levels
        self.lines = lines
    

class Hooke(BaseOscillator):
    '''harmonic (Hooke) oscillator'''
    def __init__(self, we, m1, m2, re, r = None, De=0, nu_max=100):
        '''
        Parameters
        ----------
        we : float or pint.Quantity
            wavenumber , in cm-1
        m1, m2 : float or pint.Quantity
            masses of atom 1 and atom 2, in atomic mass unit
        re : float or pint.Quantity
            equilibrium distance (bond length), in angstrom    
        r : array of float or pint.Quantity
            distances, in angstrom
        De : float or pint.Quantity
            well depth (potential energy minimum), in joule
        nu_max : int
            maximum vibrational level to consider
        '''
        if r is None:
            r = np.linspace(0*re, 5*re, 1000)
        # use quantites with units
        if not isinstance(we, pint.Quantity):
            we /= ureg.centimeter 
        if not isinstance(m1, pint.Quantity):
            m1 *= ureg.unified_atomic_mass_unit
        if not isinstance(m2, pint.Quantity):
            m2 *= ureg.unified_atomic_mass_unit
        if not isinstance(re, pint.Quantity):
            re *= ureg.angstrom
        if not isinstance(r, pint.Quantity):
            r *= ureg.angstrom
        if not isinstance(De, pint.Quantity):
            De *= ureg.joule
        self.we = we
        self.m1 = m1
        self.m1 = m2
        self.re = re
        self.r = r
        self.De = De
        self.nu_max = nu_max
        self.mu = (m1*m2)/(m1+m2) # reduced mass
        c = ureg.speed_of_light
        # force constant
        self.k = self.mu * (2 * ureg.pi * c * we)**2
        self.compute()

    def compute(self):
        '''
        compute potential and lines for energy levels
        '''
        r = self.r
        re = self.re
        k = self.k
        De = self.De
        x = r-re
        self.V = 0.5*k*x**2 - De
        self._compute_levels()

    def _energy_levels(self):
        '''
        compute vibrational energy levels
            
        Returns
        -------
        levels : array of pint.Quantity
            energy levels
        '''
        nu = np.arange(self.nu_max)
        we = self.we
        De = self.De
        h = ureg.planck_constant
        c = ureg.speed_of_light
        return ((nu + 0.5) * we * h * c) - De
    
    @classmethod
    def from_spect_data(cls, data, **kwargs):
        params = ['we', 'm1', 'm2', 're']
        return cls(**{p: data[p] for p in params}, **kwargs)
        return cls(we, m1, m2, re, **kwargs)

    
class Morse(BaseOscillator):
    '''anharmonic (Morse) oscillator'''
    def __init__(self, we, wexe, m1, m2, re, r = None, nu_max = None):
        '''
        compute Morse oscillator potential

        Parameters
        ----------
        we : float or pint.Quantity
            wavenumber , in cm-1
        wexe : float or pint.Quantity
            anharmonic parameter, in cm-1
        m1, m2 : float or pint.Quantity
            masses of atom 1 and atom 2, in atomic mass unit
        re : float or pint.Quantity
            equilibrium distance (bond length), in angstrom    
        r : array of float or pint.Quantity
            distances, in angstrom
        nu_max : int
        '''
        if r is None:
            r = np.linspace(0*re, 5*re, 1000)
        # use quantites with units
        if not isinstance(we, pint.Quantity):
            we /= ureg.centimeter 
        if not isinstance(wexe, pint.Quantity):
            wexe /= ureg.centimeter 
        if not isinstance(m1, pint.Quantity):
            m1 *= ureg.unified_atomic_mass_unit
        if not isinstance(m2, pint.Quantity):
            m2 *= ureg.unified_atomic_mass_unit
        if not isinstance(re, pint.Quantity):
            re *= ureg.angstrom
        if not isinstance(r, pint.Quantity):
            r *= ureg.angstrom
        self.we = we
        self.wexe = wexe
        self.m1 = m1
        self.m1 = m2
        self.re = re
        self.r = r
        self.mu = (m1*m2)/(m1+m2)
        self._morse_params()
        if not nu_max:
            De = self.De
            h = ureg.planck_constant
            c = ureg.speed_of_light
            nu_max = int(2*De/(h*c*we))
        self.nu_max = nu_max
        self.compute()
    
    def compute(self):
        De = self.De
        r = self.r
        re = self.re
        a = self.alfa
        x = r - re
        # attractive part of potential
        attr = -2*De*np.exp(-a*x)
        # repulsive part of potential
        rep = De*np.exp(-2*a*x)
        self.V = attr + rep
        self._compute_levels()

    def _morse_params(self):
        '''
        compute Morse oscillator parameters from specttroscopic data
        '''
        mu = self.mu
        we = self.we
        wexe = self.wexe
        c = ureg.speed_of_light
        h = ureg.planck_constant 
        De = we * we / (4 * wexe) * h * c # well depth
        self.De = De
        self.alfa = we * np.sqrt(2 * mu/De) * ureg.pi * c # exponential parameter

    def _energy_levels(self):
        '''
        compute vibrational energy levels
            
        Returns
        -------
        levels : array of pint.Quantity
            energy levels
        '''
        we = self.we
        wexe = self.wexe
        De = self.De
        nu_max = self.nu_max
        c = ureg.speed_of_light
        h = ureg.planck_constant 
        nu = np.arange(nu_max)
        levels = h*c*((nu+0.5)*we - (nu+0.5)*(nu+0.5)*wexe) - De
        return levels
    
    @classmethod
    def from_spect_data(cls, data, **kwargs):
        params = ['we', 'wexe', 'm1', 'm2', 're']
        return cls(**{p: data[p] for p in params}, **kwargs)
