# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 09:53:15 2016

@author: Jack Chen
This is the uncertainty class
"""
import numpy as np


class Uncertainty():
    def __init__(self, Z, Zinv, config, restraintpos, checkpos, nominal, beta, corrected, debug):
        self.Z = Z
        self.Zinv = Zinv
        self.config = config
        self.Q = Zinv[0:config.shape[1]:1, 0:config.shape[1]:1]
        self.B = np.dot(self.Q, np.dot(config.T, config))
        self.B = np.dot(self.B, self.B.T)
        self.restraintpos = restraintpos
        self.checkpos = checkpos
        self.calibpos = 1 - (restraintpos + checkpos)
        self.nominal = nominal
        self.beta = beta
        self.Y = corrected
        self.debug = debug

    def findRandomUncertainty(self, ranerror, sigmaw, sigmab):
        randomerr = (3 * ranerror) ** 2
        withinerr = (3 * sigmaw) ** 2
        betweenerr = (3 * sigmab) ** 2
        restraintnom = np.dot(self.restraintpos.T, self.nominal)
        diag = np.diagonal(self.Zinv)
        diag = np.atleast_2d(diag[0:len(diag) - 2]).T
        random = (self.nominal / restraintnom) ** 2 * randomerr + \
                 diag * withinerr + \
                 np.atleast_2d(np.diagonal(self.B)).T * betweenerr
        random = (random ** .5) / 3
        self.random = random

    def findEnviroUncertainty(self, temp, press, humid, airdensity, tempuncert, pressuncert, humiduncert, xcouncert,
                              coexpans, volumes, volumecov):
        if not (volumecov.shape[0]):
            volumecov = np.zeros((self.config.shape[1], 1))
        deltatemp = temp - 20
        T = temp + 273.15
        # Molar Mass Calculations
        xco2 = 0.00040  # mole fraction of CO2 in the air
        Ma = (28.96546 + 12.011 * (xco2 - 0.00040)) * 10 ** (-3)  # kg/mol molar mass of dry air
        Mv = 18.01528 * 10 ** (-3)  # kg/mol molar mass of water
        # Vapor Pressure at Saturation Calculation
        A = 1.2378847 * 10 ** (-5)  # K^(-2)
        B = -1.9121316 * 10 ** (-2)  # K^(-1)
        C = 33.93711047
        D = -6.3431645 * 10 ** 3  # K
        psv = np.exp(A * (T) ** 2 + B * (T) + C + D / (T))  # Pa water vapor pressure at saturation (function of temp)
        # print psv
        # Enhancement Factor Calculation
        alpha = 1.00062
        beta = 3.14 * 10 ** (-8)  # Pa^(-1)
        gamma = 5.6 * 10 ** (-7)  # K^(-2)
        f = alpha + beta * press + gamma * (temp) ** 2  # enhancement factor (temp is in C)
        """
        COV Rhoa-----------------------------------------------------------------------------------------------------
        """

        humiduncert = humiduncert / 100
        up = 1 / (press - .378 * humid * f * psv) * pressuncert
        ut = -1 / (T) * tempuncert
        uh = -0.3780 * f * psv / (press - 0.3780 * humid * f * psv) * humiduncert
        uxco2 = 1.4446 / (3.48374 + 1.4446 * (xco2 - 0.0004)) * xcouncert
        uz = 22 * 10 ** -6
        if self.debug == True:
            print 'up'
            print up
            print 'ut'
            print ut
            print 'uh'
            print uh
            print 'uxco2'
            print uxco2
        covrhoa = up ** 2 + ut ** 2 + uh ** 2 + uxco2 ** 2 + (uz) ** 2
        covrhoa = covrhoa ** .5 * airdensity
        covrhoa = covrhoa ** 2
        self.covrhoa = covrhoa

        if self.debug == True:
            print 'covrhoa'
            print self.covrhoa
        """
        C(rhoa)-------------------------------------------------------------------------------------------
        """
        Crhoa = np.dot(self.config, np.diag(coexpans.flatten()))
        Crhoa = np.dot(Crhoa.T, np.diag(deltatemp.flatten())).T
        Crhoa = Crhoa + self.config
        Crhoa = np.dot(Crhoa, volumes)
        self.Crhoa = Crhoa

        """
        Air density Uncertainty-------------------------------------------------------------------------------------------
        """

        QX = np.dot(self.Q, self.config.T)

        QXCrhoa = np.dot(QX, np.diag(Crhoa.flatten()))

        adUncert = np.dot(QXCrhoa, np.diag(covrhoa.flatten()))

        adUncert = np.dot(adUncert, QXCrhoa.T)

        self.airdensity = np.atleast_2d(np.diagonal(adUncert) ** .5).T

        if self.debug == True:
            print "Q*X'"
            print QX
            print "Q*X'*Crhoa"
            print QXCrhoa
        """
        C(v)-------------------------------------------------------------------------------------------
        """

        Cv = np.dot(self.config, np.diag(coexpans.flatten()))
        Cv = np.dot(Cv.T, np.diag(deltatemp.flatten())).T
        Cv = self.config + Cv
        Cv = np.dot(Cv.T, np.diag(airdensity.flatten())).T
        self.Cv = Cv

        """
        volume uncertainty-------------------------------------------------------------------------------------------
        """

        QXCv = np.dot(QX, Cv)
        QXCvcovv = np.dot(QXCv, np.diag(volumecov.flatten()) ** 2)
        vUncert = np.dot(QXCvcovv, QXCv.T)
        self.volume = np.atleast_2d(np.diagonal(vUncert) ** .5).T
        if self.debug:
            print "Q*X'*Cv"
            print QXCv
            print "Q*X'*Cv*Cov(v)"
            print QXCvcovv

    def findSystematicUncertainty(self, syserror, airTypeB, volumeTypeB):
        restraintnom = np.dot(self.nominal.T, self.restraintpos)
        typeB = self.nominal / restraintnom * syserror
        typeB = typeB ** 2 + airTypeB ** 2 + volumeTypeB ** 2
        typeB = typeB ** .5
        self.systematic = typeB