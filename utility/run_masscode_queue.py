__author__ = 'masslab'

import subprocess

path_to_masscode = r"L:\internal\684.07\Mass_Project\Software\Calibration Processor\20160412\masscomp_absoft_2016_04_11.exe"


def run_old_masscode(input_path, output_path):

    subprocess.call([path_to_masscode, str(input_path), str(output_path)])


# input_path = r"L:\internal\684.07\Mass_Project\Software\PythonProjects\measure\testing\peter\runMasscode\lbseries4_2.ntxt"
# output_path = r"L:\internal\684.07\Mass_Project\Software\PythonProjects\measure\testing\peter\runMasscode\lbseries4_2.nout"
# run_old_masscode(input_path, output_path)