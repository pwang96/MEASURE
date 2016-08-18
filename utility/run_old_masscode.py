import subprocess

path_to_masscode = r"L:\internal\684.07\Mass_Project\Software\Calibration Processor\20160412\masscomp_absoft_2016_04_11.exe"
input_path = 'L:\\internal\\684.07\\Mass_Project\\Customers\\Calibration Reports\\FLUOR\\workup\\S071\\20160808run1_1.ntxt'
output_path = 'L:\\internal\\684.07\\Mass_Project\\Customers\\Calibration Reports\\FLUOR\\workup\\S071\\20160808run1_1.nout'

subprocess.call([path_to_masscode, input_path, output_path])

print repr(input_path), '\n', repr(output_path)
