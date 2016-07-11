# -*- coding: utf-8 -*-
"""
Created on Wed Jun 01 13:45:42 2016
Mass Code
@author: jjc8
"""
import numpy as np
from air_density_solver import air_density_solver
from Uncertainty import Uncertainty


class MassCode:
    def __init__(self, massInfo, runData, debug=False, lists=True):
        """

        """
        self.debug = debug
        self.massInfo = massInfo
        self.runData = runData
        self.config = np.atleast_2d(massInfo['config'])
        print self.config
        self.Fcrit = 2.61  # alpha=.05
        self.Tcrit = 1.96  # alpha=.05
        self.takeDifferences()
        self.processEnviros()
        if self.massInfo['sensitivity'] != []:
            self.convertMass()
        self.createVolumes()
        self.correctBuoyancy()
        self.correctAddOn()
        self.doCorrections()
        self.computeFinal()
        self.iterateBuoyancyCorrect()
        self.correctGravitational()
        self.doFTest()
        self.doTTest()
        self.findUncertainty()
        if lists:
            self.makeLists()

    def takeDifferences(self):
        """
        PURPOSE
        This method takes the difference btween the observations in each comparison
        The differences are taken according to the configuration matrix.
        The method also does additional functions such as compute drift and sensititvity

        Steps:
        1. Gather data
        2. Check the number of observations for each comparision, if there are 4 assume ABBA, if 3 assume ABA
        3. Loops through each comparison and produces the difference matrix
        """

        rawData = self.runData[
            self.runData.keys()[0]]  # takes the dictionary down one level to all the obserrvations in this specific run
        """
        we want to check how many values you have to figure our the configuraitons (either ABBA or ABA)
        """
        numObs = len(rawData[rawData.keys()[0]].keys())  # number of observations per weigh
        differ = []  # the difference matrix also known as [A-B]
        sensi = []
        drift = []
        #        print numObs
        if numObs == 4:  # if ABBA
            # print("you got 4 keys")#code for testing

            for y in sorted(rawData.keys()):  # runs the loop through all the comparisons
                Observations = rawData[y]
                differ.append(float((Observations['A1'][0] + Observations['A2'][0]) - (
                Observations['B1'][0] + Observations['B2'][0])) / 2)
                sensi.append(float(
                    Observations['A2'][0] - Observations['A1'][0] + Observations['B2'][0] - Observations['B1'][0]) / 2)
                drift.append(float((Observations['B1'][0] - Observations['A1'][0]) + (
                Observations['A2'][0] - Observations['B2'][0])) / 2)

        self.difference = np.atleast_2d(differ).T  # takes the list, converts to array, makes it 2d and transposes it
        self.drift = np.atleast_2d(drift).T
        self.sensitivity = np.atleast_2d(sensi).T
        if self.debug:
            print 'difference matrix:'
            print self.difference
            # print 'sensitivity:',self.sensitivity
            # print 'drift:',self.drift

    def processEnviros(self):
        """
        PURPOSE
        This method creates a vector with the line by line air density

        Steps:
        1. Gather data and initilize
        2. Loop thorugh each comparision and get environmental readings
        3. Get the average of the environmentals for each comparison (called line by line)
        4. Use the average line by line environmetals to calculate air density

        """
        rawData = self.runData[self.runData.keys()[0]]  # 1
        temp = []  # 1
        press = []
        humid = []
        airdense = []  # 1

        tempcorr = self.massInfo['envirocorrection']['temp']
        presscorr = self.massInfo['envirocorrection']['press']
        humidcorr = self.massInfo['envirocorrection']['humid']

        if tempcorr == [] or tempcorr[1] == 0:
            tempcorr = [0, 1]
        if presscorr == [] or presscorr[1] == 0:
            presscorr = [0, 1]
        if humidcorr == [] or humidcorr[1] == 0:
            humidcorr = [0, 1]

        for x in sorted(rawData.keys()):  # 2
            temprow = []
            pressrow = []
            humidrow = []

            for y in sorted(rawData[x].keys()):
                temprow.append(float(rawData[x][y][1]))
                pressrow.append(float(rawData[x][y][2]))
                humidrow.append(float(rawData[x][y][3]))

            temprow_avg = sum(temprow) / float(len(temprow))  # 3
            pressrow_avg = sum(pressrow) / float(len(pressrow))
            humidrow_avg = sum(humidrow) / float(len(humidrow))

            # Correction
            temprow_avg = tempcorr[0] + tempcorr[1] * temprow_avg
            pressrow_avg = presscorr[0] * 133.322365 + presscorr[1] * pressrow_avg
            humidrow_avg = humidcorr[0] / 100 + humidcorr[1] * humidrow_avg

            temp.append(temprow_avg)
            press.append(pressrow_avg)
            humid.append(humidrow_avg)
            airdense.append(air_density_solver(temprow_avg, pressrow_avg, humidrow_avg))  # 4

        self.temperature = np.atleast_2d(temp).T
        self.pressure = np.atleast_2d(press).T
        self.humidity = np.atleast_2d(humid).T
        self.airdensity = np.atleast_2d(airdense).T
        self.temp = np.mean(np.array(temp))
        self.press = np.mean(np.array(press))
        self.humid = np.mean(np.array(humid))
        self.airdens = air_density_solver(self.temp, self.press, self.humid)
        if self.debug:
            print 'Average Temperature:', self.temp
            print 'Average Pressure:', self.press
            print 'Average Humidity:', self.humid
            print 'Average Air Density:', self.airdens
            print 'Line by line temperature:'
            print self.temperature
            print 'Line by line air density'
            print self.airdensity

    def convertMass(self):
        """
        PURPOSE
        This method converts the division into actual units of mass (mg) if the reading were measured with a manual balance
        with a sensitivity weight
        """
        if 0 in self.massInfo['sensitivity']:
            print 'no sensitivity weight used'
            return
        sensimass = self.massInfo['sensitivity'][0]
        sensivolume = self.massInfo['sensitivity'][1]
        sensicoexpans = self.massInfo['sensitivity'][2]
        sensiweight = sensimass - sensivolume * (1 + sensicoexpans * (self.temperature - 20) * self.airdensity)
        conversion = sensiweight / self.sensitivity  # mg/div
        self.conversion = conversion
        self.difference = self.difference * conversion
        if self.debug:
            print 'Sensitivity Mass', sensimass
            print 'Sensitivity Volume', sensivolume
            print 'Sensitivity Coefficient of Thermal Expansion', sensicoexpans
            print 'Apparent weight of sensitivity Weight at each Comparison'
            print sensiweight
            print 'Conversion in mg/div'
            print self.conversion
            print 'New difference Matrix in units of mg'
            print self.difference

    def createVolumes(self):
        """
        PURPOSE
        This method corrects the volume for thermal expansion effects

        Steps:
        1. Gather data
        2. Compute uncorrected volume
        3. Get delta T
        4. Match thermal expansion to each mass in each comparision
        5. Match each uncorrected volumes to each mass in each observation
        6. Match each average line by line temperature with the comparision or line it is from
        7. Compute the corrected volume for each mass in each comparision

        """

        volumes = self.massInfo['volume']
        self.masses = np.array(self.massInfo['nominal'])  # 1
        self.density = np.array(self.massInfo['density'])  # 1
        if volumes == []:
            volumes = np.zeros(self.config.shape[1])
        for x in range(0, len(volumes)):
            if volumes[x] == 0:
                volumes[x] = self.masses[x] / self.density[x]  # 2
        self.density = self.masses / np.array(volumes)

        self.volumes20 = np.dot(self.config, np.diag(volumes))  # 5
        thermexp = np.array(self.massInfo['coexpans'])  # 1
        deltatemp = self.temperature.flatten() - 20  # 3
        thermexp = np.absolute(np.dot(self.config, np.diag(thermexp)))  # 4

        self.volumes = self.volumes20 * (1 + np.dot(thermexp.T, np.diag(deltatemp)).T)  # 6

    def correctBuoyancy(self):
        """
        PURPOSE
        This method calculates the amount the readings need to be corrected for
        buoyancy effects

        """

        self.buoyanCorrect = self.airdensity * np.dot(self.volumes, np.ones((self.volumes.shape[1], 1)))  # 1a,b
        if self.debug:
            print'Volume correction from line by line temperature'
            print self.volumes

    def correctAddOn(self):
        """
        PURPOSE
        This method caluculates the correctiomn needed to remove any addon weights
        """
        addOn = self.massInfo['add']
        totaladdon = np.zeros((self.config.shape[0], 1))

        if addOn == [[]]:
            self.addOnCorrect = totaladdon
            return

        for x in addOn:
            position = np.diag(x[0])
            correction = np.dot(np.dot(self.config, position), np.ones((self.config.shape[1], 1)))
            if x[2] != 0:
                volume = float(x[2])
            else:
                volume = float(x[1] / x[3])
            volume = ((self.temperature - 20) * x[4] + 1) * volume
            buoyancy = volume * self.airdensity
            totaladdon = totaladdon + correction * (-x[1] * 1000)
        self.addOnCorrect = totaladdon
        if self.debug:
            print 'Addon correction:'
            print self.addOnCorrect

    def doCorrections(self):
        """
        PURPOSE
        This method applies the buoyancy and addon correction to the difference matrix

        Steps:
        1. Take Buoyancy correction
            a. Subtract the volumes of each compared mass
            b. Multiply by the line by line air density
        """

        self.Asave = self.difference + self.addOnCorrect
        self.corrected = self.Asave + self.buoyanCorrect

        if self.debug:
            print 'Buoyancy correction:'
            print self.buoyanCorrect
            print'Corrected difference matrix'
            print self.corrected
            print 'A(i)'
            print self.Asave

    def computeFinal(self):
        """
        PURPOSE
        This method does a least squares estimate of the mass correction

        Steps:
        1. Create augemented matrix Z
            a. Start with X*X^-1 the configuration matrix
            b. Add the restraint vector to the right
            c. Add X^-1*Y the configuration matrix inverse mutiplied by the corrected difference matrix
            d. Calculate the value of the restraint accepted correction
            e. Create a horizontal vector with the restraint position vector and [o,restraint correction value]
            f. Add this vector to the bottom of Z
            g. Add a row of zeros ending with -1 to the bottom of Z
        2. Take inverse of Z
        4. Find solution
        """
        #        self.corrected=np.atleast_2d([-2.9122901401770595*10**-2,.47012994147601717,-.41083282136648336,.49850000567113284,-.38147681890407625,-.88037356356793695]).T
        restraintpos = np.atleast_2d(self.massInfo['restraintpos']).T
        #        print np.dot(self.config.T,self.config)
        Z = np.append(np.dot(self.config.T, self.config), restraintpos, axis=1)  # 1a,b
        #        print Z
        Z = np.append(Z, np.dot(self.config.T, self.corrected), axis=1)  # 1c
        #        print Z
        restraint = np.dot(restraintpos.T, self.massInfo['acceptcorrect'])  # 1d
        #        print restraint
        x = np.append(restraintpos.T, [[0, restraint]], axis=1)  # 1e
        Z = np.append(Z, x, axis=0)  # 1f
        # print Z, 'shape:', self.config.shape[0]
        Z = np.append(Z, np.zeros((1, Z.shape[1])), axis=0)  # 1g
        #        print Z
        Z[Z.shape[0] - 1, Z.shape[1] - 1] = -1  # 1g
        #        print Z
        Zinv = np.linalg.inv(Z)  # 2
        self.Z = Z
        self.Zinv = Zinv
        self.correct = np.atleast_2d(Zinv[0:self.config.shape[1]:1, Z.shape[0] - 1]).T  # 4
        if self.debug:
            print 'Z matrix'
            print Z
            print 'Z inverse'
            print Zinv

    def iterateBuoyancyCorrect(self):
        """
        PURPOSE
        This method continues redoing the buoyancy correction for a more correct
        mass values until it isn't significant anymore
        """
        thermexp = np.array(self.massInfo['coexpans'])  # 1
        deltatemp = self.temperature.flatten() - 20  # 3
        thermexp = np.absolute(np.dot(self.config, np.diag(thermexp)))  # 4
        withinstd = self.massInfo['balstd'][0]
        c1 = self.volumes
        self.c1 = c1
        #print c1
        flag = True
        counter = 0
        while flag:
            betahat = np.dot(self.config, np.diag(self.correct.flatten()))
            volume = np.nan_to_num((np.dot(self.config, np.diag(self.masses)) + .001 * betahat) / np.absolute(
                np.dot(self.config, np.diag(self.density))))
            c2 = volume * (1 + np.dot(thermexp.T, np.diag(deltatemp)).T)
            #print (np.absolute(c1 - c2) < (.01 * withinstd)).all()
            if (np.absolute(c1 - c2) < (.01 * withinstd)).all():
                flag = False
            else:
                counter += 1
                if counter == 10:
                    flag = False
            c1 = c2
            self.correct2 = self.correct
            self.corrected2 = self.corrected
            self.volumes = c2
            self.correctBuoyancy()
            self.doCorrections()
            self.computeFinal()
        print c2

    def correctGravitational(self):
        """
        PURPOSE
        This method corrects the final answer for the gravitaional gradient
        """
        gradient = self.massInfo['gravgrad']
        height = np.array(self.massInfo['cgravity'])
        nominal = np.array(self.massInfo['nominal'])
        correction = np.atleast_2d(height * nominal * 1000 * gradient).T
        self.gravityCorrect = correction
        self.correct = self.correct + self.gravityCorrect
        if self.debug:
            print 'Gravity correction:'
            print self.gravityCorrect

    def doFTest(self):
        """

        """
        self.delta = self.corrected - np.dot(self.config, self.correct)
        dof = self.config.shape[0] - self.config.shape[1] + 1.0
        sd = (np.sum(self.delta ** 2) / (dof)) ** .5
        Fratio = sd ** 2 / self.massInfo['balstd'][0] ** 2
        self.sdev = sd
        self.Fratio = Fratio
        if Fratio < self.Fcrit:
            print "F RATIO IS LESS THAN  3.79 (CRITICAL VALUE FOR PROBABILITY = .01)."
            print "THEREFORE THE STANDARD DEVIATION IS IN CONTROL."
        else:
            print "F RATIO IS GREATER OR EQUAL TO  3.79 (CRITICAL VALUE FOR PROBABILITY = .01)."
            print "THEREFORE THE STANDARD DEVIATION IS NOT IN CONTROL."
        if self.debug:
            print 'Standard deviation', self.sdev
            print 'F ratio', self.Fratio
            print 'Delta'
            print self.difference

    def doTTest(self):

        self.Q = self.Zinv[0:self.config.shape[1]:1, 0:self.config.shape[1]:1]
        self.B = np.dot(self.Q, np.dot(self.config.T, self.config))
        self.B = np.dot(self.B, self.B.T)
        checkposition = np.atleast_2d(self.massInfo['checkpos']).T
        resposition = np.atleast_2d(self.massInfo['restraintpos']).T
        nominal = np.atleast_2d(self.massInfo['nominal']).T
        acceptcorrect = self.massInfo['acceptcorrect']
        sigmac = np.dot(checkposition.T, np.dot(self.Q, checkposition)) * self.massInfo['balstd'][0] ** 2 + \
                 (np.dot(checkposition.T, nominal) / np.dot(resposition.T, nominal)) ** 2 * self.massInfo['error'][
                                                                                                0] ** 2 + \
                 np.dot(checkposition.T, np.dot(self.B, checkposition)) * self.massInfo['balstd'][1] ** 2
        sigmac = sigmac ** .5
        self.Tvalue = (np.dot(checkposition.T, self.correct) - np.dot(checkposition.T, acceptcorrect)) / sigmac
        if self.debug:
            print 'sigmac', sigmac

    def findUncertainty(self):
        if self.massInfo['envirouncertainty'] == []:
            self.massInfo['envirouncertainty'] = [0, 0, 0, 0]

        self.uncert = Uncertainty(self.Z, self.Zinv, self.config, np.atleast_2d(self.massInfo['restraintpos']).T,
                                  np.atleast_2d(self.massInfo['checkpos']).T, np.atleast_2d(self.massInfo['nominal']).T,
                                  self.correct, self.corrected, self.debug)
        self.uncert.findRandomUncertainty(self.massInfo['error'][0], self.massInfo['balstd'][0],
                                          self.massInfo['balstd'][1])
        self.uncert.findEnviroUncertainty(self.temperature, self.pressure, self.humidity, self.airdensity,
                                          self.massInfo['envirouncertainty'][0], self.massInfo['envirouncertainty'][1],
                                          self.massInfo['envirouncertainty'][2], self.massInfo['envirouncertainty'][3],
                                          np.atleast_2d(self.massInfo['coexpans']).T,
                                          np.atleast_2d(self.masses / self.density).T,
                                          np.atleast_2d(self.massInfo['volumecov']).T)
        self.uncert.findSystematicUncertainty(self.massInfo['error'][1], self.uncert.airdensity, self.uncert.volume)
        self.uncertainty = (self.uncert.random ** 2 + self.uncert.systematic ** 2) ** .5
        self.expuncertainty = self.uncertainty * 2

    def makeLists(self):
        self.correct = self.correct.flatten().tolist()
        self.uncertainty = self.uncertainty.flatten().tolist()
        self.uncert.airdensity = self.uncert.airdensity.flatten().tolist()
        self.uncert.volume = self.uncert.volume.flatten().tolist()
        self.uncert.random = self.uncert.random.flatten().tolist()
        self.uncert.systematic = self.uncert.systematic.flatten().tolist()



