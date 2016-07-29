__author__ = 'masslab'

import json
import datetime


def generate_abridged_json_file(path, output, run=1):
    """
    Takes the output of the masscode and puts it into a json file

    :param path: path, chosen by the QFileDialog
    :param main_dict: the main dictionary with all the weight info and vector info
    :param data_dict: the dictionary with all the run info: readouts and environmental readings
    :param output: instance of the MassCode class
    :param run: which run number it is. This will only be inputted by the comparator
    :return: path to the json file
    """

    f_ratio = None
    t_value = None

    # ABBAs will not have this
    try:
        if output.f_ratio:
            f_ratio = output.f_ratio
        if output.t_value:
            t_value = output.t_value
    except AttributeError:
        pass

    all_info = {'average air density': output.airdens,
                'air density': output.airdensity,
                'average temperature': output.temp,
                'temperature': output.temperature,
                'average humidity': output.humid,
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
                'date': datetime.datetime.strftime(datetime.datetime.now(), "%m/%d/%Y %H:%M")}

    filename = path + "_abridged.json"

    with open(filename, 'w+') as f:
        json.dump(all_info, f)

    return filename
