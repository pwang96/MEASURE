__author__ = 'masslab'

import json
import datetime


def generate_json_file(path, main_dict, data_dict, output, run=1):
    """
    Takes the output of the masscode and puts it into a json file

    :param path: path, chosen by the QFileDialog
    :param main_dict: the main dictionary with all the weight info and vector info
    :param data_dict: the dictionary with all the run info: readouts and environmental readings
    :param output: instance of the MassCode class
    :param run: which run number it is. This will only be inputted by the comparator
    :return: path to the json file
    """

    names = []
    nominals = []
    densities = []
    exp_coeffs = []
    accepteds = []
    f_ratio = None
    t_value = None
    for i in main_dict['weight info']:
        names.append(i[0][0:15].strip())
        nominals.append(i[0][16:26].strip())
        densities.append(i[0][26:36].strip())
        exp_coeffs.append(i[0][36:46].strip())
        accepteds.append(i[0][46:].strip())

    # ABBAs will not have this
    try:
        if output.f_ratio:
            f_ratio = output.f_ratio
        if output.t_value:
            t_value = output.t_value
    except AttributeError:
        pass

    # Calculate the average air pressure
    air_pressure_sum = 0
    dct = data_dict.values()[0]
    for key in dct.keys():
        for measurement in dct[key].keys():
            air_pressure_sum += float(dct[key][measurement][2])
    avg_air_pressure = air_pressure_sum/24

    all_info = {'average air density': output.airdens,
                'air density': output.airdensity,
                'average temperature': output.temp,
                'temperature': output.temperature,
                'average humidity': output.humid,
                'average air pressure': avg_air_pressure,
                'volumes': output.volumes,
                'volumes at 20': output.volumes20,
                'differences': output.difference,
                'corrections': output.correct,
                'sensitivity': output.sensitivity,
                'drift': output.drift,
                'corrected differences': output.corrected,
                'nominal weights': output.masses,
                'densities': output.density,
                'uncertainties': output.uncertainty,
                'type A': output.uncert.random,
                'air density uncertainty': output.uncert.airdensity,
                'volume uncertainty': output.uncert.volume,
                'type B': output.uncert.systematic,
                'uncertainty': output.uncertainty,
                'expanded uncertainty': output.expuncertainty,
                'f ratio': f_ratio,
                'f crit': output.f_crit,
                't value': t_value,
                't crit': output.t_crit,
                'delta': output.delta,
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
                'date': datetime.datetime.strftime(datetime.datetime.now(), "%m-%d-%Y %H:%M")}

    all_info.update(data_dict)

    filename = path + "_" + str(run) + ".json"
    with open(filename, 'w+') as f:
        json.dump(all_info, f)

    return filename
