__author__ = 'masslab'

import datetime
import json
from subprocess import call
from threading import Thread
from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtCore import QObject, pyqtSignal
from serial import Serial
from plots.environment_plot import EnvironmentPlot
from file_generators.generate_input_file import generate_input_file
from at106h_settings import AT106HSettings
from control.recipe_maker import RecipeMaker
from control.recipe_execute import execute
from control.ingredient_methods import id_command
from config import comparator_matching, masscode_path
from utility.show_dictionary import pretty
from config import base_path, output_path
from utility.serial_ports import serial_ports
from populate_dictionary.populate_masscode_dict import populate_massInfo
from populate_dictionary.masscode_dicts import massInfo
from utility import masscode_v1, masscode_v2
from file_generators.generate_json_file import generate_json_file


class ComparatorUi(QObject):
    """ Provides functionality to the sub ui for the AT106H balance.

    The interface allows the user to establish a connection to the balance, configure the run settings, and start
    and stop the calibration.
    The instruments in use are displayed along with graphs of real time data.
    There is are timer function that update the environmentals table, and update the status browser with incoming
    messages from the BalanceControl class

    Args:
        main_dict (dictionary):  Dictionary containing relevant calibration metadata created in "MainUI" class
        db (DatabaseORM):  Instance of DatabaseORM object created in "MainUI" class
    """

    # PyQt signal-slot mechanism (signal can be emitted anywhere and its slot method is executed)
    status_signal = pyqtSignal(str)
    data_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)

    def __init__(self, main_dict=None, db=None):
        self.main_dict = main_dict
        self.db = db
        super(QObject, self).__init__()
        self.window = QtGui.QDialog(None, QtCore.Qt.WindowSystemMenuHint |
                                    QtCore.Qt.WindowTitleHint |
                                    QtCore.Qt.WindowMinMaxButtonsHint)
        self.window.setSizeGripEnabled(True)

        self.ui = uic.loadUi('sub_ui/GeneralComparatorUi.ui', self.window)
        # self.ui = uic.loadUi('GeneralComparatorUi.ui', self.window)

        self.widget_dict = {self.ui.portCombo: 1,
                            self.ui.connectButton: 1,
                            self.ui.disconnectButton: 0,
                            self.ui.startCalButton: 0,
                            self.ui.stopCalButton: 0,
                            self.ui.exitButton: 1,
                            self.ui.SettingsButton: 0,
                            self.ui.workdownCheck: 1}

        self.settings_ui_dict = {68: AT106HSettings, 69: AT106HSettings}

        self.update_widgets()

        # self.main_dict = main_dict
        self.settings_dict = {}
        self.data_dict = {}
        self.input_file_path = ""
        self.conn = None
        self.run = 0
        self.plot_active = 0
        self.progress_level = 0
        self.progress_length = 0
        self.massInfo = massInfo
        self.workdown = False

        # Set up the ui
        self.ui.progressBar.setValue(0)
        self.ui.stopCalButton.setEnabled(False)

        # Make table un editable
        self.ui.enviroTable.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)

        # Insert Temperature plot i
        self.e_plot = EnvironmentPlot()
        self.ui.enviroLayout.addWidget(self.e_plot)

        # Get serial ports on machine and populate menus
        self.ui.portCombo.addItems(serial_ports())

        # Create timer objects
        self.environment_timer = QtCore.QTimer()
        self.environment_timer.start(10000)
        self.update_environment_table()

        # Connect the event callbacks
        self.callback_connector()

        # Initialize dictionaries
        self.flags = {'connection': 0, 'settings': 0}
        self.data = {'enviro readings': [], 'balance readings': []}

        # Execute the ui
        self.window.exec_()

    def progress_slot(self):
        """ Increment the progress bar in the user interface """
        self.progress_level += 1
        value = int((float(self.progress_level)/self.progress_length)*100)
        self.ui.progressBar.setValue(value)

    def status_slot(self, args):
        """ Update the status browser with new argument """
        self.ui.statusBrowser.clear()
        self.ui.statusBrowser.append(args)

        # Detect if a balance serial connection was made, arg will include "Id response"
        if 'Id response:' in args:
            self.flags['connection'] = 1
            self.widget_dict[self.ui.SettingsButton] = 1
            self.update_widgets()

    def is_end_of_run(self):
        """ Return True if end of run detected, False otherwise"""
        runs = sorted(self.data_dict.keys())
        return all(all(x.values()) for x in self.data_dict[runs[self.run]].values())

    def cal_data_slot(self, arg):
        """ Receives balance signal readout

        Gets latest environment data, pairs it with the balance readout and updates data_dict.
        Number of current run is stored in variable "run".  If last measurement of run is detected,
        masscode input file is generated and pushed through the masscode.

        Data storage and graphing in ui to be implemented.

        """
        print 'here is the balance readout: %s' % arg
        self.e_plot.add_vertical()
        press = self.db.latest_barometer_data(self.main_dict['barometer id'])[0]
        temp = self.db.latest_thermometer_data(self.main_dict['thermometer id'])[0]
        humid = self.db.latest_hygrometer_data(self.main_dict['hygrometer id'])[0]

        runs = sorted(self.data_dict.keys())
        for key2 in sorted(self.data_dict[runs[self.run]].keys()):
            for key3 in sorted(self.data_dict[runs[self.run]][key2].keys()):
                if not self.data_dict[runs[self.run]][key2][key3]:
                    if int(self.main_dict['balance id']) == 69:
                        self.data_dict[runs[self.run]][key2][key3] = ([(1000*float(arg)), float(temp), float(press), float(humid)])
                    else:
                        self.data_dict[runs[self.run]][key2][key3] = ([float(arg), float(temp), float(press), float(humid)])
                    pretty(self.data_dict, indent=1)
                    if self.is_end_of_run():
                        # run_number = int(re.findall(r'[\d]+', runs[self.run])[0])
                        run_number = self.run + 1
                        
                        # TEMPORARY CODE, saves main dictionary for debugging purposes
                        # ---------------------------------------------------------
                        with open('%s/data_dict_%s.json' % (base_path, str(run_number)), 'w+') as fp:
                            json.dump(self.data_dict, fp)
                        # ---------------------------------------------------------
                        # Create the .ntxt file
                        input_file = generate_input_file(self.input_file_path,
                                                         self.main_dict,
                                                         self.data_dict[runs[self.run]],
                                                         run_number,
                                                         len(self.data_dict.keys()))

                        # RUN THE NEW MASSCODE
                        # TO COMMENT OUT, ADD A # AND A SPACE
                        # TO UNCOMMENT, REMOVE THE SPACE AND THE #
                        # Populate the massInfo dictionary based on the main_dict
                        # self.massInfo = populate_massInfo(self.main_dict, self.massInfo, self.workdown)

                        # dictionary with only the latest run data
                        # specific_data_dict = {runs[self.run]: self.data_dict[runs[self.run]]}

                        # output becomes MassCode object
                        # output = masscode_v2.MassCode(self.massInfo, specific_data_dict)

                        # json_file_path = generate_json_file(self.input_file_path, self.main_dict, specific_data_dict,
                        #                                     output, run_number)
                        # print json_file_path

                        # END OF NEW MASSCODE

                        # Create the output file
                        output_file = input_file[:].replace('.ntxt', '.nout')
                        print input_file
                        print output_file
                        # Run input file
                        command = '"%s" "%s" "%s"\n' % (str(masscode_path), str(input_file), str(output_file))
                        print command
                        t = Thread(target=call, args=(command,))
                        t.start()

                        # Increment run index
                        self.run += 1
                        if self.run >= len(runs):
                            self.status_signal.emit('Calibration complete!')
                            self.environment_timer.stop()
                    return

    def callback_connector(self):
        """ Activate event detection """
        self.ui.connectButton.clicked.connect(self.click_connect_bal)
        self.ui.disconnectButton.clicked.connect(self.click_disconnect_bal)
        self.ui.startCalButton.clicked.connect(self.click_start)
        self.ui.stopCalButton.clicked.connect(self.click_stop)
        self.ui.SettingsButton.clicked.connect(self.click_settings)
        self.ui.exitButton.clicked.connect(self.click_exit)
        self.status_signal.connect(self.status_slot)
        self.data_signal.connect(self.cal_data_slot)
        self.progress_signal.connect(self.progress_slot)
        self.ui.workdownCheck.stateChanged.connect(self.workdown_check)

        QtCore.QObject.connect(self.environment_timer, QtCore.SIGNAL("timeout()"), self.update_environment_table)

    def update_widgets(self):
        for value, key in self.widget_dict.items():
            value.setEnabled(key)

    def disable_widgets(self):
        for key in self.widget_dict.keys():
            self.widget_dict[key] = 0
        self.update_widgets()

    def click_settings(self):
        """ Prompt user for individualized balance settings in ui form """
        settings_ui = self.settings_ui_dict[self.main_dict['balance id']]()
        self.settings_dict = settings_ui.settings_dict
        self.flags['settings'] = 1
        self.widget_dict[self.ui.startCalButton] = 1
        self.update_widgets()

    def click_connect_bal(self):
        """ Establish serial connection with balance

        Get serial settings from main_dict (originally from database orm), and attempt to initialize a connection
        between the computer and balance.  Run the

        Raise:
            ValueError: if serial connection settings are invalid
        """
        # Disable all widgets
        self.disable_widgets()
        try:
            s = self.main_dict['balance serial settings']
            self.conn = Serial(port=None, baudrate=s[0], parity=s[1], bytesize=s[2], stopbits=s[3], timeout=s[4])
            self.conn.port = str(self.ui.portCombo.currentText())
            # Following 2 lines are perhaps slightly hard to read...
            # Explanation: we get the identify balance serial command from the comparator command dictionary in config.
            # the balance command dictionary is mapped to it's id number in the "comparator_matching dictionary"
            # Maybe this can be simplified.
            command = comparator_matching[self.main_dict['balance id']]['identify'][0][0]
            status_string = comparator_matching[self.main_dict['balance id']]['identify'][1]

            t = Thread(target=id_command, args=(self.status_signal, self.conn, command, status_string, 2))
            t.start()
        except ValueError as e:
            # Write error to status browser
            self.status_signal.emit('Error in connection object: ' + str(e))
            # Re-enable widgets
            self.widget_dict[self.ui.exitButton] = 1
            self.widget_dict[self.ui.connectButton] = 1
            self.widget_dict[self.ui.portCombo] = 1
            self.update_widgets()
        else:
            # Re-enable widgets
            self.widget_dict[self.ui.exitButton] = 1
            self.widget_dict[self.ui.disconnectButton] = 1
            self.widget_dict[self.ui.exitButton] = 1
            self.update_widgets()

    def click_disconnect_bal(self):
        """ Erase the balance serial connection object "conn" """
        self.disable_widgets()
        self.widget_dict[self.ui.exitButton] = 1
        self.widget_dict[self.ui.connectButton] = 1
        self.widget_dict[self.ui.portCombo] = 1
        self.update_widgets()
        self.ui.statusBrowser.clear()

        self.plot_active = 0

        self.flags['connection'] = 0
        self.conn = []
        self.status_signal.emit('Balance connection closed')

    def get_file_path(self):
        """ Prompt user for desired path """
        file_dialog = QtGui.QFileDialog()
        self.input_file_path = QtGui.QFileDialog.getSaveFileName(file_dialog, 'Save as...',
                                    output_path + "\\" + datetime.date.today().strftime("%Y%m%d")).replace('/', '\\')

    def click_start(self):
        """ Run the list of methods generated in "RecipeMaker" in a new thread.

        Prompts user to select a directory and calibration name.  Instantiates the recipe maker, extracts the recipe
        "m" and data dictionary "data_dict"
.  Runs "execute" in new thread, so balance method execution does
        not interfere with the ui.
        """
        self.ui.workdownCheck.setEnabled(0)
        if not all(self.flags.values()):
            self.status_signal.emit('Error: Faulty balance connection or incomplete settings')
            return

        self.get_file_path()

        # Use recipe maker to generate list of methods and method arguments
        rm = RecipeMaker(self.status_signal,
                         self.conn,
                         self.main_dict,
                         self.settings_dict,
                         comparator_matching[self.main_dict['balance id']])

        self.data_dict = rm.data_d
        self.progress_length = len(rm.m)
        self.plot_active = 1

        # Daemon thread dies when calling function is killed
        t = Thread(target=execute, args=(rm.m, rm.a, self.data_signal, self.progress_signal))
        t.setDaemon(True)
        t.start()

    def update_environment_table(self):
        """ Fetch latest environment data from database and display in environment table """
        t_row = self.db.latest_thermometer_data(self.main_dict['thermometer id'])
        p_row = self.db.latest_barometer_data(self.main_dict['barometer id'])
        h_row = self.db.latest_hygrometer_data(self.main_dict['hygrometer id'])

        for index_1, instrument in enumerate([t_row, p_row, h_row]):
            for index_2, field in enumerate(instrument):
                item = QtGui.QTableWidgetItem()
                item.setText(str(field))
                self.ui.enviroTable.setItem(index_1, index_2, item)
        self.ui.enviroTable.resizeColumnsToContents()

        if self.plot_active:
            self.e_plot.add_point(t_row[0], p_row[0], h_row[0])

    def workdown_check(self):
        if self.ui.workdownCheck.isChecked():
            self.workdown = True
            file_dialog = QtGui.QFileDialog()
            file_name = QtGui.QFileDialog.getOpenFileName(file_dialog, "Select the PREVIOUS output file", output_path,
                                                          "*.json")
            try:
                with open(str(file_name[0])) as f:
                    data = json.load(f)

                    index_of_new_restraint = data['next restraint vec'].index(1)  # which weight is the new r
                    index_of_current_restraint = self.main_dict['restraint vec'].index(1)
                    self.massInfo['acceptcorrect'][index_of_current_restraint] \
                        = data['corrections'][index_of_new_restraint]  # next restraint becomes current restraint
                    self.massInfo['error'] \
                        = [data['type A'][index_of_new_restraint], data['type B'][index_of_new_restraint]]
                    self.main_dict['restraint uncert'] = self.massInfo['error']
                print self.massInfo['acceptcorrect'], '\n', self.massInfo['error']
            except IndexError:
                pass

    def click_stop(self):
        pass

    def click_exit(self):
        quit_msg = "Are you sure you want to exit?"
        reply = QtGui.QMessageBox.question(self.ui, 'Message:', quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.__exit__()
        else:
            pass

    def __exit__(self):
        self.window.close()


