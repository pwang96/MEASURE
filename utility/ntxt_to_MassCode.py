"""
Created on Thu Jun 30 09:01:36 2016

@author: Jack Chen
I created this file to run the old mass code in python. The user can select a file to use and the python code will run it.old input files and get it into the new data structure.
"""
from utility.masscode_v2 import MassCode
from file_generators.generate_abridged_json_file import generate_abridged_json_file



"""
DATA TYPES*********************************************************************
"""

mass_info = {'nominal': []
    , 'acceptcorrect': []
    , 'cgravity': [0, 0, 0, 0]
    , 'gravgrad': 0
    , 'volume': []
    , 'density': []
    , 'coexpans': []
    , 'config': []
    , 'restraintpos': []
    , 'restraintnew': []
    , 'checkpos': []
    , 'add': []
    , 'balstd': [0, 0]
    , 'error': [0.0, 0.0]
    , 'envirouncertainty': [0, 0, 0, 0]
    , 'volumecov': []
    , 'sensitivity': [0, 0, 0]
    , 'envirocorrection': {
        'temp': [],
        'press': [],
        'humid': []
    }}

"""
*******************************************************************************
"""
def convert(dirname):
    with open(dirname, "r") as f:
        searchlines = f.readlines()

    matrixflag = False
    # Remove all the comments
    for i, line in enumerate(searchlines):
        if "!" in line:
            searchlines.remove(searchlines[i])
    for i, line in enumerate(searchlines):
        if "WEIGHT RESTRAINT" in line and not ("WEIGHT RESTRAINT NEW SERIES" in line):
            vector = map(float, line.split()[2::])
            mass_info['restraintpos'] = vector
        if "WEIGHT CHECK STANDARD" in line:
            vector = map(float, line.split()[3::])
            mass_info['checkpos'] = vector
        if "WEIGHT RESTRAINT NEW SERIES" in line:
            vector = map(float, line.split()[4::])
            mass_info['restraintnew'] = vector
        if "READ DESIGN MATRIX" in line:
            matrixstart = i
            matrixflag = True
        if "END" in line and matrixflag:
            matrixend = i
            matrixflag = False

    for x in range(matrixstart + 1, matrixend):
        mass_info['config'].append(map(float, searchlines[x].split()))

    # center of gravity
    mass_info['cgravity'] = [0] * len(vector)

    nomflag = False
    addonflag = False
    diffflag = False
    addonstart = []
    addonend = []
    voltemp = 0.0
    volcoeffients = [0.0, 0.0]
    averageenviros = False
    units = 'METRIC'

    for i, line in enumerate(searchlines):

        if "TYPE B UNCERTAINTY" in line:
            mass_info['error'][1] = float(line.split()[3])
        if "TYPE A UNCERTAINTY" in line:
            mass_info['error'][0] = float(line.split()[3])
        if "ENGLISH UNITS" in line:
            units = 'ENGLISH'
        if "TEMPERATURE" in line:
            x = line.split()
            try:
                avg_temp = (float(x[1]) + float(x[2])) / 2
                averageenviros = True
            except:
                pass
        if "PRESSURE" in line:
            x = line.split()
            try:
                avg_press = (float(x[1]) + float(x[2])) / 2
                averageenviros = True
            except:
                pass

        if "HUMIDITY" in line:
            x = line.split()
            try:
                avg_humid = (float(x[1]) + float(x[2])) / 2
                averageenviros = True
            except:
                pass

        if "READ TEMPERATURE PRESSURE HUMIDITY" in line:
            envirostart = i
            averageenviros = False
        if "END OF ENVIRONMENT" in line:
            enviroend = i
        if "TEMPERATURE COEFFICIENTS" in line:
            mass_info['envirocorrection']['temp'] = map(float, line.split()[2:4])
        if "PRESSURE COEFFICIENTS" in line:
            mass_info['envirocorrection']['press'] = map(float, line.split()[2:4])
        if "HUMIDITY COEFFICIENTS" in line:
            mass_info['envirocorrection']['humid'] = map(float, line.split()[2:4])
        if "BALANCE WITHIN STANDARD DEVIATION" in line:
            mass_info['balstd'][0] = float(line.split()[4])
        if "BALANCE BETWEEN STANDARD DEVIATION" in line:
            mass_info['balstd'][1] = float(line.split()[4])
        if "MASS VALUE SENSITIVITY WEIGHT" in line:
            mass_info['sensitivity'][0] = float(line.split()[4])
        if "VOLUME OF SENSITIVITY WEIGHT" in line:
            mass_info['sensitivity'][1] = float(line.split()[4])
        if "COEFFICIENT OF EXPANSION" in line:
            mass_info['sensitivity'][2] = float(line.split()[3])
        if "READ WEIGHT" in line:
            nomstart = i
            nomflag = True
        if "END" in line and nomflag:
            nomend = i
            nomflag = False
        if "WEIGHT VOLUME TEMPERATURE" in line:
            voltemp = float(line.split()[3])
        if "WEIGHT VOLUME COEFFICIENTS" in line:
            volcoeffients = map(float, line.split()[3:5])
        if "GRAVITY GRADIENT" in line:
            mass_info['gravgrad'] = float(line.split()[2])
            print float(line.split()[2])
        if "CENTER OF GRAVITY HEIGHT DIFFERENCE" in line:
            position = int(line.split()[5])
            center = float(line.split()[6])
            mass_info['cgravity'][position - 1] = center
        if "READ ADDON WEIGHT" in line:
            addonstart.append(i)
            addonflag = True
        if "END" in line and addonflag:
            addonend.append(i)
            addonflag = False
        if "TEMPERATURE UNCERTAINTY" in line:
            mass_info['envirouncertainty'][0] = float(line.split()[2])
        if "PRESSURE UNCERTAINTY" in line:
            mass_info['envirouncertainty'][1] = float(line.split()[2])
        if "HUMIDITY UNCERTAINTY" in line:
            mass_info['envirouncertainty'][2] = float(line.split()[2])
        if "CO2 UNCERTAINTY" in line:
            mass_info['envirouncertainty'][3] = float(line.split()[2])
        if "READ VOLUME COVARIANCE MATRIX" in line:
            volcovstart = i
        if "READ OBSERVATIONS" in line:
            diffstart = i
            diffflag = True
        if "-200000" in line:
            diffend = i
            diffflag = False
        if "END" in line and diffflag:
            diffend = i
            diffflag = False

    for x in range(nomstart + 1, nomend):
        conversion = 1
        if units == 'ENGLISH':
            conversion = 453.59237

        mass_info['nominal'].append(float(searchlines[x][16:27].strip()) * conversion)
        mass_info['density'].append(float(searchlines[x][27:37].strip()))
        mass_info['coexpans'].append(float(searchlines[x][47:58].strip()))
        try:
            mass_info['acceptcorrect'].append(float(searchlines[x][58:]))
        except:
            mass_info['acceptcorrect'].append(0)

        mass_info['volume'].append(0.0)

    for x in range(0, len(addonstart)):

        position = int(searchlines[addonstart[x]].split()[3])
        for z in range(addonstart[x] + 1, addonend[x]):
            addon = []
            addon.append([0] * len(vector))  # vector is the number of weights
            addinfo = searchlines[z].split()  # line with all the addon information
            addon[0][position - 1] = 1
            addon.append(float(addinfo[2]))
            addon.append(float(addinfo[3]))
            addon.append(float(addinfo[4]))
            addon.append(float(addinfo[1]))
            mass_info['add'].append(addon)

    if 'volcovstart' in locals():
        for x in range(volcovstart + 1, volcovstart + len(vector) + 1):
            mass_info['volumecov'].append(float(searchlines[x]))

    temp = []
    press = []
    humid = []
    ENVIlinebyline = True

    if averageenviros == False:

        for x in range(envirostart + 1, enviroend):

            enviro = searchlines[x].split()
            if enviro == []:
                break

            temp.append(float(enviro[0]))
            press.append(float(enviro[1]) * 133.322365)
            humid.append(float(enviro[2]) / 100)

        if len(temp) > len(mass_info['config']):
            temp2 = []
            press2 = []
            humid2 = []
            for x in range(0, len(temp) / 4):
                temp2.append([temp[x * 4], temp[x * 4 + 1], temp[x * 4 + 2], temp[x * 4 + 3]])
            for x in range(0, len(press) / 4):
                press2.append([press[x * 4], press[x * 4 + 1], press[x * 4 + 2], press[x * 4 + 3]])
            for x in range(0, len(humid) / 4):
                humid2.append([humid[x * 4], humid[x * 4 + 1], humid[x * 4 + 2], humid[x * 4 + 3]])
            ENVIlinebyline = False

    differ = []
    DIFFlinebyline = True
    for x in range(diffstart + 1, diffend):

        try:
            diff = float(searchlines[x])
            differ.append(diff)

        except:
            diff = searchlines[x].split()
            if len(diff) > 2:
                differ.append(map(float, diff))
                DIFFlinebyline = False
            else:
                differ.append(float(diff[0]))

    """
    creating the testData dictionary***************************
    """
    testData = {'Run': {}}
    for x in range(1, len(mass_info['config']) + 1):
        comparenum = 'Comparison' + str(x)
        ABBA = ['1-A1', '2-B1', '3-B2', '4-A2']
        testData['Run'][comparenum] = {ABBA[0]: [0, 0, 0, 0], ABBA[1]: [0, 0, 0, 0], ABBA[2]: [0, 0, 0, 0],
                                       ABBA[3]: [0, 0, 0, 0]}
        if DIFFlinebyline:
            testData['Run'][comparenum][ABBA[0]][0] = differ[x - 1] * 2
        else:
            testData['Run'][comparenum][ABBA[0]][0] = differ[x - 1][0]
            testData['Run'][comparenum][ABBA[1]][0] = differ[x - 1][1]
            testData['Run'][comparenum][ABBA[2]][0] = differ[x - 1][2]
            testData['Run'][comparenum][ABBA[3]][0] = differ[x - 1][3]
        if averageenviros == True:
            for z in ABBA:
                testData['Run'][comparenum][z][1] = avg_temp
                testData['Run'][comparenum][z][2] = avg_press
                testData['Run'][comparenum][z][3] = avg_humid
        else:
            if ENVIlinebyline:
                for z in ABBA:
                    testData['Run'][comparenum][z][1] = temp[x - 1]
                    testData['Run'][comparenum][z][2] = press[x - 1]
                    testData['Run'][comparenum][z][3] = humid[x - 1]
            else:
                for z in ABBA:
                    testData['Run'][comparenum][z][1] = temp2[x - 1][ABBA.index(z)]
                    testData['Run'][comparenum][z][2] = press2[x - 1][ABBA.index(z)]
                    testData['Run'][comparenum][z][3] = humid2[x - 1][ABBA.index(z)]

    """
    RUN************************************************************
    """
    a = MassCode(mass_info, testData, lists=False)
    generate_abridged_json_file(dirname, a)
