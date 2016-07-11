__author__ = 'masslab'

import json


def generate_json_file(path, main_dict, output):
    """
    Takes the output of the masscode and puts it into a json file

    :param path: path, chosen by the QFileDialog
    :param output: instance of the MassCode class
    :return: path to the json file
    """
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
                'restraint vec': main_dict['restraint vec'],
                'check vec': main_dict['check vec'],
                'next restraint vec': main_dict['next restraint vec']}

    filename = path + ".json"
    with open(filename, 'w+') as f:
        json.dump(all_info, f)

    return filename