__author__ = 'masslab'

import subprocess
from nist_config import nist_masscode_path


def run_masscode_queue(cls):
    # Run until queue is empty
    while not cls.input_file_queue.empty():

        input_file = cls.input_file_queue.get()

        output_file = input_file[:-3] + "out"

        # Runs the masscode
        print('"' + nist_masscode_path + '"' + "\n" + '"' + input_file + '"' + "\n" + '"' + output_file + '"' + "\n")

        #subprocess.call('"' + nist_masscode_path + '"' + "\n" + '"' + input_file + '"' + "\n" + '"' + output_file + '"' + "\n")
        proc = subprocess.Popen(nist_masscode_path, stdin=subprocess.PIPE)
        proc.communicate(input_file + '\n' + output_file + '\n')
        cls.input_file_queue.task_done()

        # Removes the input file path from the list
        try:
            cls.inputList.takeItem(0)
        except:
            pass
