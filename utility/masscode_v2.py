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
    def __init__(self, mass_info, run_data, debug=False, lists=True, validate=False):
        """
        INPUTS
        mass_info: Informationon the weights and balances being used (such as density, volume, nominal mass etc.)
        run_data: Information from the instruments during the run (such as environmental data and balance readings)
        debug: Will output in-between steps
        lists: Will convert many of the output variables from numpy arrays to lists
        validate: Will output many of the variables in a format similar to the FORTRAN masscode

        PURPOSE
        This method executes all of the methods in order
        """

        self.debug = debug
        self.mass_info = mass_info
        self.run_data = run_data
        self.config = np.atleast_2d(mass_info['config'])

        self.f_crit = 2.61  # alpha=.05
        self.t_crit = 1.96  # alpha=.05

        self.take_differences()
        self.process_enviros()
        if self.mass_info['sensitivity'] != []:
            self.convert_mass()
        self.create_volumes()
        self.correct_buoyancy()
        self.correct_addon()
        self.do_corrections()
        self.compute_final()
        self.iterate_buoyancy_correct()
        if not (self.config.shape[0] == 1):  # If the design is not ABBA
            self.do_f_test()
        self.correct_gravitational()
        # Note this is after F Test but before the T Test because the
        # deltas must be calculated without gravitational adjustment

        if not (self.config.shape[0] == 1):  # If the design is not ABBA
            self.do_t_test()
        self.find_uncertainty()
        if validate:
            self.validate()
        if lists:
            self.make_lists()

    def take_differences(self):
        """
        PURPOSE
        This method takes the difference btween the observations in each comparison
        The differences are taken according to the configuration matrix.
        The method also does additional functions such as compute drift and sensititvity

        STEPS
        1. Gather data
        2. Check the number of observations for each comparision, if there are 4 assume ABBA
        3. Loops through each comparison and produces the difference matrix
        """

        rawData = self.run_data[
            self.run_data.keys()[0]]  # takes the dictionary down one level to all the observations in this specific run
        numObs = len(rawData[rawData.keys()[0]].keys())  # number of observations per weigh
        differ = []  # the difference matrix also known as [A-B]
        sensi = []
        drift = []
        #        print numObs
        if numObs == 4:  # if ABBA
            # print("you got 4 keys") # code for testing

            for y in sorted(rawData.keys()):  # runs the loop through all the comparisons
                observations = rawData[y]
                differ.append((float(observations['1-A1'][0])
                                    + float(observations['4-A2'][0])
                                    - float(observations['2-B1'][0])
                                    - float(observations['3-B2'][0])) / 2
                              )

                sensi.append((float(observations['1-A1'][0])
                                   - 3 * float(observations['2-B1'][0])
                                   + 3 * float(observations['3-B2'][0])
                                   - float(observations['4-A2'][0])) / 2
                             )

                drift.append((float(observations['2-B1'][0])
                                   - float(observations['1-A1'][0])
                                   + float(observations['4-A2'][0])
                                   - float(observations['3-B2'][0])) / 2
                             )

        self.difference = np.atleast_2d(differ).T  # takes the list, converts to array, makes it 2d and transposes it
        self.drift = np.atleast_2d(drift).T
        self.sensitivity = np.atleast_2d(sensi).T
        if self.debug:
            print 'difference matrix:'
            print self.difference
            # print 'sensitivity:',self.sensitivity
            # print 'drift:',self.drift

    def process_enviros(self):
        """
        PURPOSE
        This method creates vectors for line by line average tmerature, pressure, humidity and air density as well as
        computing the overall mean temperature, pressure, humidity and air density.

        Steps:
        1. Gather data and initilize
        2. Loop thorugh each comparision and get environmental readings
        3. Get the average of the environmentals for each comparison (called line by line)
        4. Correct the environmentals
        5. Use the average line by line environmentals to calculate air density

        """
        rawData = self.run_data[self.run_data.keys()[0]]  # 1
        temp = []  # 1
        press = []
        humid = []
        airdense = []  # 1

        tempcorr = self.mass_info['envirocorrection']['temp']
        presscorr = self.mass_info['envirocorrection']['press']
        humidcorr = self.mass_info['envirocorrection']['humid']

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
            airdensrow = []

            for y in sorted(rawData[x].keys()):
                temprow.append(tempcorr[0] + tempcorr[1] * float(rawData[x][y][1]))

                # If pressure is in Pa, don't correct. Else if it is in mmHg, correct it to Pa by mult. by 133.322365
                if float(rawData[x][y][2]) > 5000:
                    pressrow.append(presscorr[0] * 133.322365 + presscorr[1] * float(rawData[x][y][2]))
                else:
                    pressrow.append(presscorr[0] * 133.322365 + presscorr[1] * float(rawData[x][y][2] * 133.322365))

                # If humidity is in ppm, don't correct. Else if in %RH, correct to ppm
                if float(rawData[x][y][3]) < 1:
                    humidrow.append(humidcorr[0] / 100 + humidcorr[1] * float(rawData[x][y][3]))
                else:
                    humidrow.append(humidcorr[0] / 100 + humidcorr[1] * float(rawData[x][y][3] / 100))

                airdensrow.append(air_density_solver(temprow[-1], pressrow[-1], humidrow[-1]))

            temprow_avg = sum(temprow) / float(len(temprow))  # 3
            pressrow_avg = sum(pressrow) / float(len(pressrow))
            humidrow_avg = sum(humidrow) / float(len(humidrow))
            airdenserow_avg = sum(airdensrow) / float(len(airdensrow))

            # for y in sorted(rawData[x].keys()):
            #     temprow.append(float(rawData[x][y][1]))
            #     pressrow.append(float(rawData[x][y][2]))
            #     humidrow.append(float(rawData[x][y][3]))
            # temprow_avg = sum(temprow) / float(len(temprow))  # 3
            # pressrow_avg = sum(pressrow) / float(len(pressrow))
            # humidrow_avg = sum(humidrow) / float(len(humidrow))
            #
            # #4
            # temprow_avg = tempcorr[0] + tempcorr[1] * temprow_avg
            # pressrow_avg = presscorr[0] * 133.322365 + presscorr[1] * pressrow_avg
            # humidrow_avg = humidcorr[0] / 100 + humidcorr[1] * humidrow_avg

            temp.append(temprow_avg)
            press.append(pressrow_avg)
            humid.append(humidrow_avg)
            # airdense.append(air_density_solver(temprow_avg,pressrow_avg,humidrow_avg))#5
            airdense.append(airdenserow_avg)

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

    def convert_mass(self):
        """
        PURPOSE
        This method converts the division into actual units of mass (mg) if the reading were \
        measured with a manual balance with a sensitivity weight.

        STEPS
        1. Figure out if a sensitivity weight is being used
        2. Correct weight for buoyancy
        3. Find the readings for sensitivity at each step
        4. Converts readings to sensitivity
        """
        if 0 in self.mass_info['sensitivity']:  # 1
            if self.debug:
                print 'no sensitivity weight used'
            return

        sensimass = self.mass_info['sensitivity'][0]
        sensivolume = self.mass_info['sensitivity'][1]
        sensicoexpans = self.mass_info['sensitivity'][2]

        sensiweight = sensimass - sensivolume * (1 + sensicoexpans * (self.temperature - 20) * self.airdensity)  # 2
        conversion = sensiweight / self.sensitivity  # 3,4 in mg/div

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

    def create_volumes(self):
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

        volumes = self.mass_info['volume']
        self.masses = np.array(self.mass_info['nominal'])  # 1
        self.density = np.array(self.mass_info['density'])  # 1

        if volumes == []:
            volumes = np.zeros(self.config.shape[1])

        for x in range(0, len(volumes)):
            if volumes[x] == 0:
                volumes[x] = self.masses[x] / self.density[x]  # 2

        self.density = self.masses / np.array(volumes)
        self.volumes20 = np.dot(self.config, np.diag(volumes))  # 5

        thermexp = np.array(self.mass_info['coexpans'])  # 1
        deltatemp = self.temperature.flatten() - 20  # 3
        thermexp = np.absolute(np.dot(self.config, np.diag(thermexp)))  # 4

        self.volumes = self.volumes20 * (1 + np.dot(thermexp.T, np.diag(deltatemp)).T)  # 6
        thermexp = np.array(self.mass_info['coexpans'])  # 1
        # self.airdensity = np.atleast_2d([1.1885326856826171,1.1885720676274685,1.188605743990387,1.188647982119678,1.1886926651424587,1.188745597459137]).T

        if self.debug:
            self.b2 = np.dot(np.diag(thermexp), self.config.T)
            self.b2 = np.dot(self.b2, np.diag(deltatemp)) + self.config.T
            self.b2 = np.dot(self.b2, np.diag(self.airdensity.flatten()))
            print "b2 (the airdensity times the thermal expansion)"
            print self.b2

    def correct_buoyancy(self):
        """
        PURPOSE
        This method calculates the amount the readings need to be corrected for buoyancy effects
        STEPS
        1. Multiply air density by volume to find buoyancy correction
        """

        self.buoyan_correct = self.airdensity * np.dot(self.volumes, np.ones((self.volumes.shape[1], 1)))  # 1

        if self.debug:
            print'Volume correction from line by line temperature'
            print self.volumes

    def correct_addon(self):
        """
        PURPOSE
        This method caluculates the correctiomn needed to remove any addon weights
        STEPS
        1. Initialize
        2. Check if addon weights are present
        3. Find the postiion of the weight
        4. Find the buoyancy correcvtion to the mass
        5. Add the corrected mass to the  addon correction vector
        """
        addon = self.mass_info['add']  # 1
        totaladdon = np.zeros((self.config.shape[0], 1))
        self.madd = np.zeros((self.config.shape[0], 1))
        self.badd = np.zeros((self.config.shape[0], 1))

        if addon == [[]]:  # 2
            self.addon_correct = totaladdon
            return

        for x in addon:
            position = np.atleast_2d(x[0]).T  # 3
            correction = np.dot(self.config, position)
            if x[2] != 0:  # 4
                volume = float(x[2])
            else:
                volume = float(x[1] / x[3])
            volume = ((self.temperature - 20) * x[4] + 1) * volume
            buoyancy = volume * self.airdensity
            # buoyancy = 0
            totaladdon = totaladdon + correction * (buoyancy - x[1] * 1000)  # 5

            self.madd = self.madd + correction * x[1] * 1000
            self.badd = self.badd + correction * buoyancy

        self.addon_correct = totaladdon

        if self.debug:
            print 'Addon correction:'
            print self.addon_correct
            print "Madd (Total mass of addon)"
            print self.madd
            print "BADD (Total buoyancy correction of addon)"
            print self.badd

    def do_corrections(self):
        """
        PURPOSE
        This method applies the buoyancy and addon correction to the difference matrix

        Steps:
        1. Take Buoyancy correction
            a. Subtract the volumes of each compared mass
            b. Multiply by the line by line air density
        """

        self.a_save = self.difference + self.addon_correct
        self.corrected = self.a_save + self.buoyan_correct

        if self.debug:
            print 'Buoyancy correction:'
            print self.buoyan_correct
            print'Corrected difference matrix'
            print self.corrected
            print 'A(i)'
            print self.a_save

    def compute_final(self):
        """
        PURPOSE
        This method does a least squares estimate of the mass correction

        Steps:
        1. Create augmented matrix Z
            a. Start with X*X^-1 the configuration matrix
            b. Add the restraint vector to the right
            c. Add X^-1*Y the configuration matrix inverse multiplied by the corrected difference matrix
            d. Calculate the value of the restraint accepted correction
            e. Create a horizontal vector with the restraint position vector and [o,restraint correction value]
            f. Add this vector to the bottom of Z
            g. Add a row of zeros ending with -1 to the bottom of Z
        2. Take inverse of Z
        4. Find solution
        """
        # self.corrected = np.atleast_2d(
        #     [-2.9122901401770595 * 10 ** -2, .45368241721295988, -.42459212610918939, .48205143095474057,
        #      -.39523712978514425, -.87768456174130649]).T
        restraintpos = np.atleast_2d(self.mass_info['restraintpos']).T
        #        print np.dot(self.config.T,self.config)
        Z = np.append(np.dot(self.config.T, self.config), restraintpos, axis=1)  # 1a,b
        #        print Z
        Z = np.append(Z, np.dot(self.config.T, self.corrected), axis=1)  # 1c
        #        print Z
        restraint = np.dot(restraintpos.T, self.mass_info['acceptcorrect'])  # 1d
        #        print restraint
        x = np.append(restraintpos.T, [[0, restraint]], axis=1)  # 1e
        Z = np.append(Z, x, axis=0)  # 1f
        #        print Z
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

    def iterate_buoyancy_correct(self):
        """
        PURPOSE
        This method continues redoing the buoyancy correction for a more correct
        mass values until it isn't significant anymore
        STEPS
        1. Initialize
        2. Start iterations withthe current corrected volumes 'c1'
        3. Create the new volumes 'c2' based off of the corrected weights (instead of using nominal)
        4. Run through the new calculations of betahat
        5. Sytop if the different volumes differ by less than .01 the standard deviation of the balance
        """
        # self.corrected = np.atleast_2d(
        #     [-2.9122901401770595 * 10 ** -2, .45359553931807284, -.42454872240239183, .48196454751122531,
        #      -.39519372290446597, -.87755426235087186]).T
        thermexp = np.array(self.mass_info['coexpans'])  # 1
        deltatemp = self.temperature.flatten() - 20
        thermexp = np.absolute(np.dot(self.config, np.diag(thermexp)))
        withinstd = self.mass_info['balstd'][0]
        c1 = self.volumes  # 2
        self.c1 = c1

        if self.debug:
            print 'Old Volumes at T'
            print c1

        flag = True
        counter = 0
        while flag:
            volume = np.nan_to_num((np.dot(self.config, np.diag(self.masses + .001 * self.correct.flatten()))) \
                                   / np.absolute(np.dot(self.config, np.diag(self.density))))

            c2 = volume * (1 + np.dot(thermexp.T, np.diag(deltatemp)).T)  # 3

            self.correct2 = self.correct  # 4
            self.corrected2 = self.corrected

            if self.debug:
                print 'Old correcton (betahats)'
                print self.correct
                print 'Old Corrected Difference Matrix (Y)'
                print self.corrected

            self.volumes = c2
            self.correct_buoyancy()
            self.do_corrections()
            self.compute_final()
            self.b1 = volume
            self.b2 = self.buoyan_correct / np.dot(self.b1, np.ones((self.b1.shape[1], 1)))

            if self.debug:
                print "b1 (new volumes)"
                print self.b1
                print 'The Difference bBetween Old and Revised Buoyancy Correciton'
                print (self.corrected2 - self.corrected)

            if np.absolute(self.corrected2 - self.corrected < (.000000001)).all():  # 5
                flag = False
            else:
                counter += 1
                if counter == 10:
                    flag = False
            # counter += 1
            # if counter == 5:
            #     flag = False
            c1 = c2

    def correct_gravitational(self):
        """
        PURPOSE
        This method corrects the final answer for the gravitational gradient
        STEPS
        1. Initilize
        2. Multiply height difference by gradient
        3. Correct the betahat values
        """
        gradient = self.mass_info['gravgrad']  # 1
        height = np.array(self.mass_info['cgravity'])
        nominal = np.array(self.mass_info['nominal'])

        correction = np.atleast_2d(height * nominal * 1000 * gradient).T  # 2

        self.gravity_correct = correction
        self.correct = self.correct + self.gravity_correct  # 3

        if self.debug:
            print 'Gravity correction:'
            print self.gravity_correct

    def do_f_test(self):
        """
        PURPOSE
        The F test is to figure out if the solution does not deviate beyond historical data
        STEPS
        1. Solve for delta
        2. Find the degrees of freedom
        3. Find the sandard deviaiton of the solution
        4. Find the F ratio
        """
        self.delta = self.corrected - np.dot(self.config, self.correct)  # 1
        dof = self.config.shape[0] - self.config.shape[1] + 1.0  # 2
        sd = (np.sum(self.delta ** 2) / (dof)) ** .5  # 3

        f_ratio = sd ** 2 / self.mass_info['balstd'][0] ** 2  # 4

        self.sdev = sd
        self.f_ratio = f_ratio

        if self.debug:
            print 'Standard deviation', self.sdev
            print 'F ratio', self.f_ratio
            print 'Delta'
            print self.difference

    def do_t_test(self):
        """
        PURPOSE
        The T test checks for the deviatioin of the check weight from the historical correction to the check weights
        STEPS
        1. Initialize
        2. Solve for sigma c
        3. Calculate a student T test
        """
        self.Q = self.Zinv[0:self.config.shape[1]:1, 0:self.config.shape[1]:1]  # 1
        self.B = np.dot(self.Q, np.dot(self.config.T, self.config))
        self.B = np.dot(self.B, self.B.T)

        checkposition = np.atleast_2d(self.mass_info['checkpos']).T
        resposition = np.atleast_2d(self.mass_info['restraintpos']).T
        nominal = np.atleast_2d(self.mass_info['nominal']).T
        acceptcorrect = self.mass_info['acceptcorrect']

        # 2
        sigmac = np.dot(checkposition.T, np.dot(self.Q, checkposition)) * self.mass_info['balstd'][0] ** 2 \
                 + (np.dot(checkposition.T, nominal) / np.dot(resposition.T, nominal)) ** 2 * self.mass_info['error'][
                                                                                                  0] ** 2 \
                 + np.dot(checkposition.T, np.dot(self.B, checkposition)) * self.mass_info['balstd'][1] ** 2
        sigmac = sigmac ** .5

        self.sigmac = sigmac

        accepted = np.dot(checkposition.T, acceptcorrect)
        observed = np.dot(checkposition.T, self.correct)

        self.t_value = (observed - accepted) / sigmac  # 3
        self.t_value = self.t_value.flatten()[0]

        if self.debug:
            print 'Observed', observed
            print 'Accepted', accepted
            print 'sigmac', sigmac
            print 't_value', self.t_value

    def find_uncertainty(self):
        """
        PURPOSE
        This method find the uncertainty through the class Uncertainty
        STEPS
        1. Get random (Type A) uncertainty
        2. Get air density uncertainty
        3. Get volume uncertainty
        4. Get total systematic (Type B) uncertainty
        5. Get total standard and expanded uncertainty

        """
        if self.mass_info['envirouncertainty'] == []:
            self.mass_info['envirouncertainty'] = [0, 0, 0, 0]

        self.uncert = Uncertainty(self.Z,
                                  self.Zinv,
                                  self.config,
                                  np.atleast_2d(self.mass_info['restraintpos']).T,
                                  np.atleast_2d(self.mass_info['checkpos']).T,
                                  np.atleast_2d(self.mass_info['nominal']).T,
                                  self.correct, self.corrected, self.debug
                                  )

        self.uncert.findRandomUncertainty(self.mass_info['error'][0],
                                          self.mass_info['balstd'][0],
                                          self.mass_info['balstd'][1]
                                          )

        self.uncert.findEnviroUncertainty(self.temperature,
                                          self.pressure,
                                          self.humidity,
                                          self.airdensity,
                                          self.mass_info['envirouncertainty'][0],
                                          self.mass_info['envirouncertainty'][1],
                                          self.mass_info['envirouncertainty'][2],
                                          self.mass_info['envirouncertainty'][3],
                                          np.atleast_2d(self.mass_info['coexpans']).T,
                                          np.atleast_2d(self.masses / self.density).T,
                                          np.atleast_2d(self.mass_info['volumecov']).T
                                          )

        self.uncert.findSystematicUncertainty(self.mass_info['error'][1],
                                              self.uncert.airdensity,
                                              self.uncert.volume
                                              )

        self.uncertainty = (self.uncert.random ** 2 + self.uncert.systematic ** 2) ** .5

        self.expuncertainty = self.uncertainty * 2

    def make_lists(self):
        """
        PURPOSE
        This method makes the major outputs into lists for easier data processing outside of the mass code.
        STEPS

        """
        self.correct = self.correct.flatten().tolist()

        self.airdensity = self.airdensity.flatten().tolist()
        self.humidity = self.humidity.flatten().tolist()
        self.pressure = self.pressure.flatten().tolist()
        self.temperature = self.temperature.flatten().tolist()

        # Now we need to average the volumes for each mass.
        average_volumes = []
        num_volumes = self.volumes.shape[1]
        for x in range(0, num_volumes):
            average_volumes.append(sum(abs(self.volumes[:, x])) / sum(self.volumes[:, x] != 0))
        self.volumes = average_volumes

        average_volumes20 = []
        num_volumes = self.volumes20.shape[1]
        for x in range(0, num_volumes):
            average_volumes20.append(sum(abs(self.volumes20[:, x])) / sum(self.volumes20[:, x] != 0))
        self.volumes20 = average_volumes20

        self.difference = self.difference.flatten().tolist()
        self.sensitivity = self.sensitivity.flatten().tolist()
        self.drift = self.drift.flatten().tolist()

        self.masses = self.masses.tolist()
        self.density = self.density.tolist()

        self.corrected = self.corrected.flatten().tolist()
        try:
            self.delta = self.delta.flatten().tolist()
        except Exception:
            self.delta = 0

        self.uncertainty = self.uncertainty.flatten().tolist()
        self.expuncertainty = self.expuncertainty.flatten().tolist()
        self.uncert.airdensity = self.uncert.airdensity.flatten().tolist()
        self.uncert.volume = self.uncert.volume.flatten().tolist()
        self.uncert.random = self.uncert.random.flatten().tolist()
        self.uncert.systematic = self.uncert.systematic.flatten().tolist()

    def validate(self):
        print 'ACCEPTED WITHIN STANDARD DEVIATION OF THE PROCESS', self.mass_info['balstd'][0]
        print 'ACCEPTED BETWEEN STANDARD DEVIATION OF THE PROCESS', self.mass_info['balstd'][1]
        print 'RESTRAINT VECTOR', self.mass_info['restraintpos']
        # print 'MASS CORRECTION OF RESTRAINT'
        print 'TYPE B UNCERTAINTY IN THE RESTRAINT', self.mass_info['error'][1]
        print 'TYPE A UNCERTAINTY AFFECTING RESTRAINT', self.mass_info['error'][0]
        print 'CHECK STANDARD VECTOR', self.mass_info['checkpos']
        # print 'ACCEPTED MASS CORRECTION OF CHECK STANDARD'
        # print 'REPORT VECTOR'
        print 'NOMINAL VALUE [g]', self.masses
        print 'DENSITY [g/cm^3 @ 20 C]', self.density
        print 'COEFFICIENT OF EXPANSION', self.mass_info['coexpans']
        print 'ACCEPTED CORRECTION'
        print self.mass_info['acceptcorrect']
        print 'CALIBRATION DESIGN'
        print self.config
        print 'OBSERVATIONS IN DIVISIONS DIRECT READING'
        print self.difference
        print 'ADJUSTED A(I) [mg]'
        print self.corrected
        print "DELTA (I) [mg]"
        print self.delta
        print 'ITEM [g]'
        print self.masses
        print 'CORRECTION [mg]'
        print self.correct
        print 'VOLUME (AT T) [cm^3]'
        print self.config * self.volumes
        print 'TYPE B UNCERT [mg]'
        print self.uncert.systematic
        print 'TYPE A UNCERT [mg]'
        print self.uncert.random
        print 'EXPANDED UNCERT [mg]'
        print self.expuncertainty
        print 'OBSERVED STANDARD DEVIATION OF THE PROCESS'
        print self.sdev
        print 'ACCEPTED STANDARD DEVIATION OF THE PROCESS'
        print self.mass_info['balstd'][0]
        # print 'DEGREES OF FREEDOM'
        print 'F RATIO', self.f_ratio
        if self.f_ratio < self.f_crit:
            print "F RATIO IS LESS THAN  2.61 (CRITICAL VALUE FOR PROBABILITY = .05)."
            print "THEREFORE THE STANDARD DEVIATION IS IN CONTROL."
        else:
            print "F RATIO IS GREATER OR EQUAL TO  2.61 (CRITICAL VALUE FOR PROBABILITY = .05)."
            print "THEREFORE THE STANDARD DEVIATION IS NOT IN CONTROL."
        print 'CHECK STANDARD VECTOR', self.mass_info['checkpos']
        # print 'ACCEPTED MASS CORRECTION OF CHECK STANDARD'
        # print 'OBSERVED CORRECTION OF CHECK STANDARD'
        print 'STANDARD DEVIATION OF THE OBSERVED CORRECTION', self.sigmac
        print 'T VALUE', self.t_value
        if self.t_value < self.t_crit:
            print "ABSOLUTE VALUE OF T IS LESS THAN 1.96 (ALPHA = 0.050)."
            print "THEREFORE CHECK STANDARD IS IN CONTROL."
        else:
            print "ABSOLUTE VALUE OF T IS GREATER THAN 1.96 (ALPHA = 0.050)."
            print "THEREFORE CHECK STANDARD IS NOT IN CONTROL."

        # print 'TYPE B UNCERTAINTY [mg]'
        # print 'TYPE A UNCERTAINTY [mg]'
        # print 'EXPANDED UNCERTAINTY [mg]'
        print 'CORRECTED TEMPERATURE [C]'
        print self.temperature
        print 'CORRECTED PRESSURE [mmHg]'
        print self.pressure
        print 'CORRECTED HUMIDITY [rh]'
        print self.humidity
        print 'COMPUTED AIR DENSITY [mg/cm^3]'
        print self.airdensity

        # print 'INPUT FILE--------------------------------------------'
        # print 'TYPE A UNCERTAINTY'
        # print 'TYPE B UNCERTAINTY'
        # print 'READ TEMPERATURE PRESSURE HUMIDITY'
        # print 'Nominal value of weight (g)'
        # print 'Density of weight {g/cm^3)'
        # print 'Coeffficent of thermal expansion (1/C)'
        # print 'Accepted correction (mg)'
        # print 'WEIGHT RESTRAINT'
        # print 'WEIGHT CHECK STANDARD'
        # print 'WEIGHT RESTRAINT NEW SERIES'
        # print 'WEIGHT PRINT'
        # print 'READ DESIGN MATRIX'
        # print 'READ OBSERVATIONS'
