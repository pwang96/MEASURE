__author__ = 'masslab'

import json
import datetime


def generate_json_file(path, main_dict, data_dict, output):
    """
    Takes the output of the masscode and puts it into a json file

    :param path: path, chosen by the QFileDialog
    :param main_dict: the main dictionary with all the weight info and vector info
    :param data_dict: the dictionary with all the run info: readouts and environmental readings
    :param output: instance of the MassCode class
    :return: path to the json file
    """

    names = []
    nominals = []
    densities = []
    exp_coeffs = []
    accepteds = []

    for i in main_dict['weight info']:
        names.append(i[0][0:15].strip())
        nominals.append(i[0][16:26].strip())
        densities.append(i[0][26:36].strip())
        exp_coeffs.append(i[0][36:46].strip())
        accepteds.append(i[0][46:].strip())

    all_info = {'average air density': output.airdens.flatten().tolist(),
                'air density': output.airdensity.flatten().tolist(),
                'average temperature': output.temp.flatten().tolist(),
                'temperature': output.temperature.flatten().tolist(),
                'average humidity': output.humid.flatten().tolist(),
                'volumes': output.volumes.flatten().tolist(),
                'differences': output.difference.flatten().tolist(),
                'corrections': output.correct,
                'sensitivity': output.sensitivity.flatten().tolist(),
                'drift': output.drift.flatten().tolist(),
                'corrected differences': output.corrected.flatten().tolist(),
                'nominal weights': output.masses.flatten().tolist(),
                'densities': output.density.flatten().tolist(),
                'uncertainties': output.uncertainty,
                'type A': output.uncert.random,
                'air density uncertainty': output.uncert.airdensity,
                'volume uncertainty': output.uncert.volume,
                'type B': output.uncert.systematic,
                'uncertainty': output.uncertainty,
                'expanded uncertainty': output.expuncertainty.flatten().tolist(),
                'f ratio': output.Fratio,
                'f crit': output.Fcrit,
                't value': output.Tvalue,
                't crit': output.Tcrit,
                'delta': output.delta.flatten().tolist(),
                'restraint vec': main_dict['restraint vec'],
                'check vec': main_dict['check vec'],
                'next restraint vec': main_dict['next restraint vec'],
                # From this point on will be balance info, non processed stuff
                'balance id': main_dict['balance id'],
                'balance name': main_dict['balance name'],
                'balance std': [0.01, main_dict['balance std dev']],
                'barometer id': main_dict['barometer id'],
                'design id': main_dict['design id'],
                'design matrix': main_dict['design matrix'],
                'check between': main_dict['check between'],
                'hygrometer id': main_dict['hygrometer id'],
                'pressure uncert': main_dict['pressure uncert'],
                'humidity uncert': main_dict['humidity uncert'],
                'restraint uncert': main_dict['restraint uncert'],
                'temperature uncert': main_dict['temperature uncert'],
                'thermometer id': main_dict['thermometer id'],
                'weight names': names,
                'weight nominals': nominals,
                'weight densities': densities,
                'weight exp coefficients': exp_coeffs,
                'weight accepted values': accepteds,
                'date': datetime.datetime.strftime(datetime.datetime.now(), "%m/%d/%Y %H:%M")}

    all_info.update(data_dict)

    filename = path + ".json"
    with open(filename, 'w+') as f:
        json.dump(all_info, f)

    return filename