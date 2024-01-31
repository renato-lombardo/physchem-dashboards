import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from numpy.random import default_rng
from plotly.subplots import make_subplots


def normpdf(x, mean, sd):
    ''' compute normal probability density function'''
    var = sd**2
    denom = (2*np.pi*var)**.5
    num = np.exp(-(x-mean)**2/(2*var))
    return num/denom


def Ehrenfest(nA=10, nB=10, nsteps=100, width=100., height=100):
    """
    Generator functions that simulates Ehrenfest model for
    ideal gas expansion.
    Klein, M. J. Entropy and the Ehrenfest Urn Model. Physica 1956, 22 (6), 569–575.
    https://doi.org/10.1016/S0031-8914(56)90001-5.

    Each step yelds the configuration after a new extraction
    in the model
    
    Parameters
    ----------
    nA, nB : int
        number of particles in box A and box B, respectively
    nsteps : int
        number of steps (extractions) to run
    width, height : float
        box dimensions
    
    Return
    X, Y : array
        X and Y coordinates for the particles in the box
    fA, fB : float
        fraction of particles in box A and box B respect
    hist : array
        histogram of fluctuations
    hist_fit : array
        gaussian fit for the histogram   
    """
    # initialize random number generator
    rng = default_rng()
    n = nA + nB # total number of particles
    # generate random coordinates for particles in the box
    XY = rng.random((n, 2))*np.array((width, height))
    # Assign nA particles in box A and nB in box B
    A = np.zeros(len(XY),dtype=bool) # mask for box A
    A[:nA] = True
    B = np.invert(A) # mask for box B
    X = XY[:,0]
    Y = XY[:,1]
    # add box witdh to X coordinates of particles in box B
    # in order to plot them in the box B
    X[B] += width # particles in B are in the right box
    # fA, fB and fluctuation are lists storing a value for each step
    fA = [A.sum()/n,] # fraction of particles in A 
    fB = [B.sum()/n,] # fraction of particles in B
    fluctuation = [B.sum()-A.sum(),]
    # compute istogram of fluctuation
    bins = np.arange(-n, n+1, 1)
    hist = np.histogram(fluctuation, bins=bins, density=True)
    # initialize histogram fit (none for first step)
    hist_fit = [[],[]]
    # yield first configuration
    yield X, Y, fA, fB, hist, hist_fit
    # yield nsteps configurations
    for step in range(nsteps):
        i = rng.choice(len(XY), 1) # choose random particle
        A[i] = not A[i] # move the particle from one box
        B[i] = not B[i] # to the other
        if B[i]: # if the particles moved from A to B
            X[i] += width # add box width to X coordinate
        else: # if particle moved from B to A
            X[i] -= width # subtract box width to X coordinate
        # append new fraction values for this step
        fA.append(A.sum()/n)
        fB.append(B.sum()/n)
        # append new fluctuation value for this step
        fluctuation.append(B.sum()-A.sum())
        # calculate new histogram with current data
        hist = np.histogram(fluctuation, bins=bins, density=True)
        # fit a gaussian distribution to the histogram
        fluct_arr = np.array(fluctuation)
        hist_fit = normpdf(hist[1], fluct_arr.mean(), fluct_arr.std())
        yield X, Y, fA, fB, hist, hist_fit
    return