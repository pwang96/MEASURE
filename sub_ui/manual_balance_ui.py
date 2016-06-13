__author__ = 'masslab'

import datetime
import json
import re
from subprocess import call
from threading import Thread
from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtCore import QObject, pyqtSignal
from serial import Serial
from plots.environment_plot import EnvironmentPlot
from file_generators.generate_input_file import generate_input_file
from control.recipe_maker import RecipeMaker
from control.recipe_execute import execute
from control.ingredient_methods import id_command
from config import comparator_matching, masscode_path
from utility.show_dictionary import pretty
from config import base_path
from utility.serial_ports import serial_ports


class ManualBalanceUI(QObject):
    """ Provides functionality to the sub ui for manual balances.

    The interface allows the user to establish a connection to the balance and run a manual calibration.
    The interface (status browser) will tell the user which weights to put on and when to remove them.



    Args:
        main_dict (dictionary):  Dictionary containing relevant calibration metadata created in "MainUI" class
        db (DatabaseORM):  Instance of DatabaseORM object created in "MainUI" class
    """

    # PyQt signal-slot mechanism (signal can be emitted anywhere and its slot method is executed)
    status_signal = pyqtSignal(str)
    data_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)

    def __init__(self, main_dict, db):

        super(QObject, self).__init__()
        self.window = QtGui.QDialog(None, QtCore.Qt.WindowSystemMenuHint |
                                    QtCore.Qt.WindowTitleHint |
                                    QtCore.Qt.WindowMinMaxButtonsHint)

        self.window.setSizeGripEnabled(True)

        # load the UI
        self.ui = uic.loadUi('sub_ui/ManualBalanceUI.ui', self.window)

        # Execute the ui
        self.window.exec_()