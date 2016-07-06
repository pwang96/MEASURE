__author__ = 'masslab'

import datetime
import time
import json
import re
from subprocess import call
from threading import Thread
from multiprocessing.pool import ThreadPool
from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtCore import QObject, pyqtSignal, Qt, QTimer
from PyQt4.QtGui import QApplication, QCursor
from serial import Serial
from file_generators.generate_input_file import generate_input_file
from control.manual_recipe_maker import manual_short_command
from control.manual_recipe_maker import manual_id_command, manual_short_command_no_resp
from config import comparator_matching, masscode_path, massInfo
from utility.show_dictionary import pretty
from config import base_path
from utility.serial_ports import serial_ports
import Queue
from PyQt4.QtTest import QTest

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

        # Create the timers
        self.stab_timer = QTimer()

        # Populate the weights/positions table
        self.populate_reminder_table(cls)

        # Populate the port combo box with available COM ports
        self.ui.portCombo.addItems(serial_ports())

        # Disable the continue button until a connection is established
        self.ui.continueButton.setEnabled(0)

        # Set the minimum and maximum of the progress bar. Max will be the number of rows in the design matrix
        self.ui.progressBar.setMinimum(0)
        self.ui.progressBar.setMaximum(len(self.main_dict['design matrix']))

        # Set the font size of the status browser and set to read only
        self.ui.statusBrowser.setReadOnly(True)
        self.ui.statusBrowser.setFontPointSize(20)

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

        # stability time in seconds
        self.stab_time = 5
        self.og_stab_time = 5

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
        self.ui.stabTimeEdit.returnPressed.connect(self.ui.connectButton.click)
        self.ui.connectButton.clicked.connect(self.click_connect)
        self.status_signal2.connect(self.status_slot2)
        self.ui.workdownCheck.stateChanged.connect(self.workdown_check)
        self.stab_timer.timeout.connect(self.stab_timer_slot)

    def stab_timer_slot(self):
        if self.stab_time > 0:
            self.status_signal2.emit('Stabilization time remaining: ' + str(self.stab_time))
            self.stab_time -= 1
        else:
            self.stab_timer.stop()
            self.status_signal2.emit('Taking reading..')
            self.stab_time = self.og_stab_time

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

            # TODO: call the masscode here and return the results
            # If it is a workdown, save in json file and call json file when workdown finishes
            # There might be a better way to assign all the values to the massInfo dictionary
            # massInfo['nominal'] =
            # massInfo['acceptcorrect']   # IF STATEMENT NEEDED FOR WORKDOWNS.
            # massInfo['cgravity']
            # massInfo['gravgrad']
            # massInfo['volume']
            # massInfo['coexpans']
            # massInfo['config']
            # massInfo['restraintpos']
            # massInfo['checkpos']
            # massInfo['restraintnew']
            # massInfo['add']
            # massInfo['balstd']
            # massInfo['error']
            # massInfo['envirouncertainty']
            # massInfo['volumecov']
            # massInfo['sensitivity']

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

            self.stab_timer.start(1000)  # start the timer for the stabilization time countdown

            QTest.qWait(self.og_stab_time*1000 + 1000)  # wait the same amount of time for the countdown to finish

            command = comparator_matching[self.main_dict['balance id']]['read'][0][0]
            status_string = comparator_matching[self.main_dict['balance id']]['read'][1]

            # --------------------------
            pool = ThreadPool(processes=2)

            # log_result will be called when the separate thread has finished running. Puts the result in a Queue
            q = Queue.Queue()

            def log_result(arg):
                q.put(arg)

            # use apply_async to start an asynchronous thread
            result = pool.apply_async(manual_short_command,
                                      args=(self.status_signal2, self.conn, command, status_string, 2),
                                      callback=log_result)

            while not result.ready():
                time.sleep(1)

            # --------------------------
            self.readout = q.get()

            # Open the motorized door if there is one
            try:
                command = comparator_matching[self.main_dict['balance id']]['open door'][0][0]
                status_string = comparator_matching[self.main_dict['balance id']]['open door'][1]
                t = Thread(target=manual_short_command_no_resp, args=(self.status_signal2, self.conn, command, status_string, self.readout))
                t.start()
            except Exception:
                print 'no motorized door'
                self.status_signal2.emit('Got reading: %s. Press Continue.' % self.readout)

            self.save_data()  # save the current readout and environmentals into the dictionary

            QApplication.restoreOverrideCursor()
            self.ui.continueButton.setEnabled(1)

            if self.step == 4:  # at step 4, it enters the B2A2 phase
                self.AB = 2
            elif self.step == 8:  # at the end of B2A2, shift back into A1B1 mode and move to next row
                self.AB = 1
                self.row_counter += 1
                self.step = 0
                # Increment the progress bar
                self.ui.progressBar.setValue(self.row_counter)

            self.isMeasure = False
            self.step += 1

        elif self.set == 1:
            weights = []  # These are the weights that will be put on
            # Look at which weights need to be put on and display the weight names
            for weightNum in set1:
                weights.append(str(weightNum) + ' - ' + str(self.ui.weightReminder.item(weightNum-1, 0).text()))
            self.status_signal2.emit('Put on weight(s): %s \nPress Continue when loaded.' % weights)
            self.isMeasure = True
            if self.AB == 1:
                self.set = 2
            self.step += 1

        elif self.set == 2:
            weights = []  # same as above
            # same as above
            for weightNum in set2:
                weights.append(str(weightNum) + ' - ' + str(self.ui.weightReminder.item(weightNum-1, 0).text()))
            self.status_signal2.emit('Put on weight(s): %s \nPress Continue when loaded.' % weights)
            self.isMeasure = True
            if self.AB == 2:
                self.set = 1
            self.step += 1

    def status_slot2(self, args):
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
            self.ui.workdownCheck.setEnabled(0)

        return

    def populate_reminder_table(self, cls):

        m = len(self.main_dict['design matrix'][0])
        self.ui.weightReminder.setRowCount(m)
        self.ui.weightReminder.setColumnCount(2)
        self.ui.weightReminder.setHorizontalHeaderLabels(["Weight", "Role"])

        for i in range(m):  # go row by row first
            for j in range(2):  # then go column by column
                if j == 0:
                    item = QtGui.QTableWidgetItem()
                    text = str(cls.ui.weightTable.item(i, j).text()).split('|')[-1].strip()  # take the item from the main UI
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
            between the computer and balance.  Communicate with the balance in another thread, t.

            Raise:
                ValueError: if serial connection settings are invalid
            """

        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

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

            # Read the stabilization time
            self.stab_time = int(self.ui.stabTimeEdit.text())

            if self.stab_time == '':
                self.stab_time = 35
            self.og_stab_time = self.stab_time
            QApplication.restoreOverrideCursor()

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

    def workdown_check(self):
        if self.ui.workdownCheck.isChecked():

            file_dialog = QtGui.QFileDialog()
            file_name = QtGui.QFileDialog.getOpenFileNames(file_dialog, "Select the PREVIOUS output file", base_path,
                                                            "*.nout")
            try:
                with open(str(file_name[0]), 'r') as f:
                    text = f.readline()
                    this = text[0:5]
                    # TODO: Parse this output file for whatever we need
                print this
            except IndexError:
                pass

    def cancel(self):
        self.window.close()

    def __exit__(self):
        self.window.close()