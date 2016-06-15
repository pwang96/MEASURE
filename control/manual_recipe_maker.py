__author__ = 'masslab'

from ingredient_methods import wait_time, short_command, short_command_no_resp, long_command, stab_time,\
    read_value_repeatedly


class ManualRecipeMaker:
    """ Generate a list of methods that will take the mass balance through a calibration

    Args:
        status_signal (pyqtSignal): pyqtSignal object declared in "ComparatorUi"
        conn (serial): Serial connection object
        main_dict (dictionary):  Relevant calibration metadata
        settings_dict (dictionary): Specific balance and run settings from balance settings ui
        instruction_dict (dictionary):  Balance commands and statuses from config file
    """
    def __init__(self, status_signal, conn, main_dict, settings_dict, instruction_dict):
        self.ss = status_signal
        self.c = conn
        self.m_d = main_dict
        self.s_d = settings_dict
        self.i_d = instruction_dict
        self.m = []
        self.a = []
        self.data_d = {}
        self.runs = 5  # Number of runs you want to do??????
        self.make_recipe()

    def make_recipe(self):
        pass
