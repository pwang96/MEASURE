__author__ = 'masslab'

import datetime
import time
import json
import re
from subprocess import call
from threading import Thread
from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtCore import QObject, pyqtSignal, Qt
from PyQt4.QtGui import QApplication, QCursor
from serial import Serial
from file_generators.generate_input_file import generate_input_file
from control.manual_recipe_maker import manual_short_command
from control.manual_recipe_maker import manual_id_command
from config import comparator_matching, masscode_path
from utility.show_dictionary import pretty
from config import base_path
from utility.serial_ports import serial_ports

try:
    _encoding = QtGui.QApplication.UnicodeUTF8

    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class ManualBalanceUI(QObject):
    """ Provides functionality to the sub ui for manual balances.

    The interface allows the user to establish a connection to the balance and run a manual calibration.
    The interface (status browser) will tell the user which weights to put on and when to remove them.



    Args:
        cls:  Instance of MainUI object
    """

    # PyQt signal-slot mechanism (signal can be emitted anywhere and its slot method is executed)
    status_signal2 = pyqtSignal(str)
    data_signal = pyqtSignal(str)

    def __init__(self, cls):

        super(QObject, self).__init__()
        self.main_dict = cls.main_dict
        self.db = cls.db

        self.window = QtGui.QDialog(None, QtCore.Qt.WindowSystemMenuHint |
                                    QtCore.Qt.WindowTitleHint |
                                    QtCore.Qt.WindowMinMaxButtonsHint)

        self.window.setSizeGripEnabled(True)

        # load the UI
        self.ui = uic.loadUi('sub_ui/ManualBalanceUI.ui', self.window)

        # Populate the weights/positions table
        self.populate_reminder_table(cls)

        # Populate the port combo box with available COM ports
        self.ui.portCombo.addItems(serial_ports())

        # Disable the continue button until a connection is established
        self.ui.continueButton.setEnabled(0)

        # start the callback connector
        self.callbackconnector()

        # initialize the variables used in proceed()
        self.row_counter = 0  # which row of the design matrix are we on?
        self.isMeasure = False  # is this a measuring round?
        self.set = 1  # which set to put on?
        self.AB = 1  # which round of the ABBA are we on? 1: A1B1, 2: B2A2
        self.step = 1  # which step are we on? 8 steps per cycle
        self.readout = 0  # balance readout
        self.run = 1  # how many runs we're doing (will be 1 for manual)

        # stability time in seconds. maybe should be worked into the UI
        self.stab_time = 5

        # initialize the flags dictionary
        self.flags = {'connection': 0, 'settings': 0}

        # initialize the data dictionary
        # makes the right number of keys
        keys = ["run " + str(i+1).zfill(2) for i in range(self.run)]
        self.data_dict = dict.fromkeys(keys)
        for key in self.data_dict.keys():
            self.data_dict[key] = dict.fromkeys(['observation ' + str(i).zfill(2) for i in range((len(self.main_dict['design matrix'])))])
            for key2 in self.data_dict[key].keys():
                self.data_dict[key][key2] = dict.fromkeys(['Set1 1', 'Set2 1', 'Set2 2', 'Set1 2'])

        # Execute the ui
        self.window.exec_()

    def callbackconnector(self):
        self.ui.continueButton.clicked.connect(self.proceed)
        self.ui.cancelButton.clicked.connect(self.cancel)
        self.ui.connectButton.clicked.connect(self.click_connect)
        self.status_signal2.connect(self.status_slot)

    def proceed(self):
        # This updates the status dialog box, and tells the user what to do next.
        # It will also tell the user what is happening. The continue button will be
        # disabled when the balance is taking a reading. When the balance finishes
        # taking a reading, the button will enable, and the status bar will tell the user
        # to click continue after completing the instructions.

        # If the row counter is past the number of design matrix rows, save everything and quit
        if self.row_counter >= len(self.main_dict['design matrix']):
            self.status_signal2.emit('Finished with measurements.')
            # Prompt user for desired path
            file_dialog = QtGui.QFileDialog()
            input_file_path = QtGui.QFileDialog.getSaveFileName(file_dialog, 'Save as...',
                                                                base_path + "\\" + datetime.date.today().strftime(
                                                                         "%Y%m%d")).replace('/', '\\')

            self.isMeasure = False  # put variables to 0 so no if statements will run
            self.set = 0

            runs = sorted(self.data_dict.keys())
            input_file = generate_input_file(input_file_path,
                                             self.main_dict,
                                             self.data_dict[runs[self.run-1]],
                                             1,
                                             len(self.data_dict.keys()))
            output_file = input_file[:].replace('.ntxt', '.nout')

            # Run input file
            command = '"%s" "%s" "%s"\n' % (str(masscode_path), str(input_file), str(output_file))
            print command
            t = Thread(target=call, args=(command,))
            t.start()

            self.window.close()

        try:
            row = self.main_dict['design matrix'][self.row_counter]  # becomes a row of the design matrix e.g. 1 -1 0 0
            set1 = [a + 1 for a, b in enumerate(row) if b == 1]  # set1 is all the weights with a 1 in the design matrix
            set2 = [a + 1 for a, b in enumerate(row) if
                    b == -1]  # set2 is all the weights with a -1 in the design matrix
        except IndexError:
            pretty(self.data_dict)

        if self.isMeasure:  # if a weight was just loaded, isMeasure will be True.

            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

            self.ui.continueButton.setEnabled(0)  # disable the continue button
            time.sleep(float(self.stab_time))  # wait the stability time before taking a reading

            command = comparator_matching[self.main_dict['balance id']]['read'][0][0]
            status_string = comparator_matching[self.main_dict['balance id']]['read'][1]
            # self.readout = the measurement
            self.readout = manual_short_command(self.status_signal2, self.conn, command, status_string, 2)

            self.save_data()

            self.status_signal2.emit('Got measurement: %s Press continue.' % str(self.readout))
            QApplication.restoreOverrideCursor()
            self.ui.continueButton.setEnabled(1)

            if self.step == 4:  # at step 4, it enters the B2A2 phase
                self.AB = 2
            elif self.step == 8:  # at the end of B2A2, shift back into A1B1 mode and move to next row
                self.AB = 1
                self.row_counter += 1
                self.step = 0

            self.isMeasure = False
            self.step += 1

        elif self.set == 1:

            self.status_signal2.emit('Put on weight(s): %s and press Continue.' % str(set1))
            self.isMeasure = True
            if self.AB == 1:
                self.set = 2
            self.step += 1

        elif self.set == 2:

            self.status_signal2.emit('Put on weight(s): %s and press Continue.' % str(set2))
            self.isMeasure = True
            if self.AB == 2:
                self.set = 1
            self.step += 1

    def status_slot(self, args):
        """ Update the status browser with new argument """
        self.ui.statusBrowser.clear()
        self.ui.statusBrowser.append(args)

        # Detect if a balance serial connection was made, arg will include "Id response"
        if 'STD' in args:
            self.flags['connection'] = 1
            self.ui.statusBrowser.clear()
            self.ui.statusBrowser.append("Connected. Press continue")
            self.ui.continueButton.setEnabled(1)
            self.ui.portCombo.setEnabled(0)
            self.ui.connectButton.setEnabled(0)
            self.ui.stabTimeEdit.setEnabled(0)

    def populate_reminder_table(self, cls):

        m = len(self.main_dict['design matrix'][0])
        self.ui.weightReminder.setRowCount(m)
        self.ui.weightReminder.setColumnCount(2)
        self.ui.weightReminder.setHorizontalHeaderLabels(["Weight", "Role"])

        for i in range(m):  # go row by row first
            for j in range(2):  # then go column by column
                if j == 0:
                    item = QtGui.QTableWidgetItem()
                    text = cls.ui.weightTable.item(i, j).text()  # take the item from the main UI
                    item.setText(text)
                    self.ui.weightReminder.setItem(i, j, item)  # and copy it into this table
                else:
                    item = QtGui.QTableWidgetItem()
                    text = cls.ui.weightTable.cellWidget(i, j).currentText()
                    item.setText(text)
                    self.ui.weightReminder.setItem(i, j, item)

            # Set Row name
            item = QtGui.QTableWidgetItem()
            cls.ui.weightTable.setVerticalHeaderItem(i, item)
            item = cls.ui.weightTable.verticalHeaderItem(i)
            item.setText("Pos. %s" % (i + 1))

    def click_connect(self):
        """ Establish serial connection with balance

            Get serial settings from main_dict (originally from database orm), and attempt to initialize a connection
            between the computer and balance.  Run the

            Raise:
                ValueError: if serial connection settings are invalid
            """

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

            t = Thread(target=manual_id_command, args=(self.status_signal2, self.conn, command, status_string, 2))
            t.start()
            self.stab_time = self.ui.stabTimeEdit.text()
            if self.stab_time == '':
                self.stab_time = 35
        except ValueError as e:
            # Write error to status browser
            self.status_signal2.emit('Error in connection object: ' + str(e))

    def save_data(self):
        # Get the latest temperatures
        press = self.db.latest_barometer_data(self.main_dict['barometer id'])[0]
        temp = self.db.latest_thermometer_data(self.main_dict['thermometer id'])[0]
        humid = self.db.latest_hygrometer_data(self.main_dict['hygrometer id'])[0]

        if self.step == 2:
            self.data_dict['run ' + str(self.run).zfill(2)]['observation ' + str(self.row_counter).zfill(2)]['Set1 1'] \
                = [str(self.readout), temp, press, humid]

        elif self.step == 4:
            self.data_dict['run ' + str(self.run).zfill(2)]['observation ' + str(self.row_counter).zfill(2)]['Set2 1'] \
                = [str(self.readout), temp, press, humid]

        elif self.step == 6:
            self.data_dict['run ' + str(self.run).zfill(2)]['observation ' + str(self.row_counter).zfill(2)]['Set2 2'] \
                = [str(self.readout), temp, press, humid]

        elif self.step == 8:
            self.data_dict['run ' + str(self.run).zfill(2)]['observation ' + str(self.row_counter).zfill(2)]['Set1 2'] \
                = [str(self.readout), temp, press, humid]

    def cancel(self):
        self.window.close()

    def __exit__(self):
        self.window.close()