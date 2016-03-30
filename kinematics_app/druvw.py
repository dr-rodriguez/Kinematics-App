#!/usr/bin/python

"""
David Rodriguez

Package containing UVW and XYZ functions
"""

from math import cos, sin
from astropy.coordinates import SkyCoord
import numpy as np

# ===================================================
# Function to calculate UVW given RA, Dec, Distance, RV, and PMs
def uvw(ra,dec,d,pmra,pmde,rv):
    k = 4.74047 #Equivalent of 1 A.U/yr in km/s
    A00 = 0.0548755604
    A01 = 0.8734370902
    A02 = 0.4838350155
    A10 = 0.4941094279
    A11 = -0.4448296300
    A12 = 0.7469822445
    A20 = -0.8676661490
    A21 = -0.1980763734
    A22 = 0.4559837762

    # Set as arrays in case ra, dec, etc were lists
    ra = np.array(ra)
    dec = np.array(dec)
    d = np.array(d)
    rv = np.array(rv)
    pmra = np.array(pmra)
    pmde = np.array(pmde)

    radcon = 3.1415926/180 # radian conversion factor

    try:
        cosd = cos(dec * radcon)
        sind = sin(dec * radcon)
        cosa = cos(ra * radcon)
        sina = sin(ra * radcon)
    except TypeError:
        cosd = np.array(map(cos,dec * radcon))
        sind = np.array(map(sin,dec * radcon))
        cosa = np.array(map(cos,ra * radcon))
        sina = np.array(map(sin,ra * radcon))

    vec1 = rv
    plx = 1000./d
    vec2 = k * pmra/plx
    vec3 = k * pmde/plx

    u = (A00*cosa*cosd + A01*sina*cosd + A02*sind) * vec1 + \
        (-A00*sina + A01*cosa) * vec2 + \
        (-A00*cosa*sind - A01*sina*sind + A02*cosd) * vec3
    v = (A10*cosa*cosd + A11*sina*cosd + A12*sind) * vec1 + \
        (-A10*sina + A11*cosa) * vec2 + \
        (-A10*cosa*sind - A11*sina*sind + A12*cosd) * vec3
    w = (A20*cosa*cosd + A21*sina*cosd + A22*sind) * vec1 + \
        (-A20*sina + A21*cosa) * vec2 + \
        (-A20*cosa*sind - A21*sina*sind + A22*cosd) * vec3
    u = -u

    return u,v,w


# ===================================================
# Function to XYZ given RA, Dec, and Distance
def xyz(ra,dec,d):

    ra = np.array(ra)
    dec = np.array(dec)
    d = np.array(d)

    c = SkyCoord(ra=ra, dec=dec, frame='icrs', unit='deg')
    l,b = c.galactic.l.radian,c.galactic.b.radian

    try:
       xgc = d * cos(b) * cos(l)
       ygc = d * cos(b) * sin(l)
       zgc = d * sin(b)
    except TypeError:
        xgc = d * map(cos,b) * map(cos,l)
        ygc = d * map(cos,b) * map(sin,l)
        zgc = d * map(sin,b)

   # See http://www.astro.virginia.edu/class/majewski/astr551/lectures/COORDS/coords.html

    return xgc,ygc,zgc

# ===================================================

version = '1.1'

