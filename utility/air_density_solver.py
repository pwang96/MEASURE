import numpy
from math import *

# This is a transcription of air_density_solver.m, written by Alexander Moses,
# transcribed by Peter Wang.


def air_density_solver(temp, press, humid):

    """
    Solves for air density using temperature, pressure, and humidity measurements.
    Equation from CIPM-2007
    :param temp: C
    :param press: Pa
    :param humid: RH
    :return: air density in kg/m3
    """

    # Inputs
    t = temp + 273.15  # Celsius to Kelvin
    p = press
    h = humid

    # Constants
    R = 8.314472  # J/mol*K molar gas constant

    # Molar Mass Calculations
    xco2 = 0.00040  # mole fraction of CO2 in the air
    Ma = (28.96546 + 12.011 * (xco2 - 0.00040)) * 10**(-3)  # kg/mol molar mass of dry air
    Mv = 18.01528 * 10**(-3)  # kg/mol molar mass of water

    # Vapor Pressure at Saturation Calculation
    A = 1.2378847 * 10**(-5)  # K^(-2)
    B = -1.9121316 * 10**(-2)  # K^(-1)
    C = 33.93711047
    D = -6.3431645 * 10**3  # K
    psv = exp(A*t**2 + B*t + C + D/t)  # Pa water vapor pressure at saturation (function of temp)

    # Enhancement Factor Calculation
    alpha = 1.00062
    beta = 3.14 * 10**(-8)  # Pa^(-1)
    gamma = 5.6 * 10**(-7)  # K^(-2)
    f = alpha + beta*p + gamma*(temp)**2  # enhancement factor (temp is in C)

    # Mole fraction of water vapor
    xv = h*f*psv/p

    # Compressibility Factor Calculation
    a0 = 1.58123 * 10**(-6)  # KPa^(-1)
    a1 = -2.9331 * 10**(-8)  # Pa^(-1)
    a2 = 1.1043 * 10**(-10)  # K^(-1) Pa^(-1)
    b0 = 5.707 * 10**(-6)  # KPa^(-1)
    b1 = -2.051 * 10**(-8)  # Pa^(-1)
    c0 = 1.9898 * 10**(-4)  # KPa^(-1)
    c1 = -2.376 * 10**(-6)  # Pa^(-1)
    d = 1.83 * 10**(-11)  # K^2 Pa^(-2)
    e = -0.765 * 10**(-8)  # K^2 Pa^(-2)
    Z = 1 - (p/t)*(a0 + a1*temp + a2*temp**2 + (b0+b1*temp)*xv + (c0 + c1*temp)*xv**2) + (p**2/t**2)*(d + e*xv**2)

    # Density Calculation
    return ((p*Ma)/(Z*R*t))*(1 - xv*(1 - (Mv/Ma)))  # kg/m3
