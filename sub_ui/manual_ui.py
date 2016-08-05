__author__ = 'masslab'

import datetime
import time
import json
import os
from subprocess import call
from threading import Thread
from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtCore import QObject, pyqtSignal, Qt, QTimer
from PyQt4.QtGui import QApplication, QCursor
from file_generators.generate_input_file import generate_input_file
from file_generators.generate_json_file import generate_json_file
from config import masscode_path
from populate_dictionary.populate_masscode_dict import populate_massInfo
from populate_dictionary.masscode_dicts import massInfo
from utility.show_dictionary import pretty
from config import base_path, output_path
from PyQt4.QtTest import QTest
from utility import masscode_v2
from sub_ui.workdown_ui import WorkdownUI

try:
    _encoding = QtGui.QApplication.UnicodeUTF8

    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class ManualUI(QtGui.QWidget):
    """ Provides functionality to the sub ui for balances with no computer connection.

    This will allow users to manually enter the balance readout.
    Environmental readings will automatically be taken, and the results will be run
    through the mass code.


    Args:
        cls:  Instance of MainUI object
    """

    # PyQt signal-slot mechanism (signal can be emitted anywhere and its slot method is executed)
    status_signal3 = pyqtSignal(str)
    data_signal = pyqtSignal(str)

    def __init__(self, cls):

        super(QtGui.QWidget, self).__init__()
        self.main_dict = cls.main_dict
        self.db = cls.db

        self.window = QtGui.QDialog(None, QtCore.Qt.WindowSystemMenuHint |
                                    QtCore.Qt.WindowTitleHint |
                                    QtCore.Qt.WindowMinMaxButtonsHint)

        self.window.setSizeGripEnabled(True)
        self.setFocusPolicy(Qt.ClickFocus)

        # load the UI
        self.ui = uic.loadUi('sub_ui/ManualUI.ui', self.window)

        # Create the timers
        self.stab_timer = QTimer()

        # Populate the weights/positions table
        self.populate_reminder_table(cls)

        # Construct the recent history table
        self.ui.historyTable.setColumnCount(4)
        self.ui.historyTable.setHorizontalHeaderLabels(["Measurement", "Temp", "Pressure", "Humidity"])
        self.ui.historyTable.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)

        # Disable everything until the stabilization time has been set
        self.ui.readoutEdit.setEnabled(0)
        self.ui.continueButton.setEnabled(0)
        self.ui.okButton.setEnabled(0)

        # Set the minimum and maximum of the progress bar. Max will be the number of rows in the design matrix
        self.ui.progressBar.setMinimum(0)
        self.ui.progressBar.setMaximum(len(self.main_dict['design matrix']))

        # Set the font size of the status browser and set to read only
        self.ui.statusBrowser3.setReadOnly(True)
        self.ui.statusBrowser3.setFontPointSize(20)
        self.ui.statusBrowser3.append("Please enter a stabilization time!")

        # start the callback connector
        self.callbackconnector()

        # initialize the variables used in proceed()
        self.row_counter = 0  # which row of the design matrix are we on?
        self.waiting = False  # has a weight just been put on?
        self.get_readout = False  # is the user going to enter a measurement?
        self.set = 1  # which set to put on?
        self.AB = 1  # which round of the ABBA are we on? 1: A1B1, 2: B2A2
        self.step = 1  # which step are we on? 8 steps per cycle
        self.readout = 0  # balance readout
        self.press = self.db.latest_barometer_data(self.main_dict['barometer id'])[0]
        self.temp = self.db.latest_thermometer_data(self.main_dict['thermometer id'])[0]
        self.humid = self.db.latest_hygrometer_data(self.main_dict['hygrometer id'])[0]
        self.run = 1  # how many runs we're doing (will be 1 for manual)
        self.input_file_path = ''  # input file path

        # stability time in seconds
        self.stab_time = 35
        self.og_stab_time = 35

        # initialize the flags dictionary
        self.flags = {'connection': 0, 'settings': 0}

        # initialize the data dictionary
        # makes the right number of keys
        keys = ["run " + str(i+1).zfill(2) for i in range(self.run)]
        self.data_dict = dict.fromkeys(keys)
        for key in self.data_dict.keys():
            self.data_dict[key] = dict.fromkeys(['observation ' + str(i+1).zfill(2) for i in range((len(self.main_dict['design matrix'])))])
            for key2 in self.data_dict[key].keys():
                self.data_dict[key][key2] = dict.fromkeys(['1-A1', '2-B1', '3-B2', '4-A2'])

        # initialize the massInfo dictionary
        self.massInfo = massInfo

        # Execute the ui
        self.window.exec_()

    def callbackconnector(self):
        self.ui.continueButton.clicked.connect(self.proceed)
        self.ui.cancelButton.clicked.connect(self.cancel)
        self.ui.stabEdit.returnPressed.connect(self.ui.okButton.click)
        self.ui.stabEdit.textChanged.connect(self.enable_ok)
        self.ui.okButton.clicked.connect(self.click_ok)
        self.status_signal3.connect(self.status_slot3)
        self.stab_timer.timeout.connect(self.stab_timer_slot)
        self.ui.readoutEdit.returnPressed.connect(self.ui.continueButton.click)
        self.ui.workdownButton.clicked.connect(self.click_workdown)
        self.ui.redoButton.clicked.connect(self.click_redo)

    def enable_ok(self):
        if not self.ui.okButton.isEnabled():
            self.ui.okButton.setEnabled(1)

    def stab_timer_slot(self):
        if self.stab_time > 0:
            self.status_signal3.emit('Stabilization time remaining: ' + str(self.stab_time))
            self.stab_time -= 1
            self.ui.readoutEdit.setEnabled(0)
        else:
            self.stab_timer.stop()
            self.status_signal3.emit('Enter measurement below')
            self.stab_time = self.og_stab_time
            self.ui.readoutEdit.setEnabled(1)
            self.ui.readoutEdit.setFocus()

            QtGui.QSound("utility/cashtill.wav").play()

    def click_redo(self):
        QtGui.QMessageBox.information(self, 'Sorry!',
                                            'This button hasn\'t been implemented yet', QtGui.QMessageBox.Ok)

    def proceed(self):
        # This updates the status dialog box, and tells the user what to do next.
        # It will also tell the user what is happening.

        # If the row counter is past the number of design matrix rows, save everything and quit
        if self.row_counter >= len(self.main_dict['design matrix']):

            # Get the measurement from the edit line
            self.readout = float(self.ui.readoutEdit.text())
            self.ui.readoutEdit.clear()

            self.update_history_table(self.readout, self.temp, self.press, self.humid)  # update the history table
            self.save_data()  # save the current readout and environmentals into the dictionary
            self.quicksave()  # save the latest info into the temp file
            self.get_readout = False
            
            self.status_signal3.emit('Finished with measurements. Generating input file.')
            
            self.ui.continueButton.setEnabled(0)  # Disable continue button while file is being written
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

            self.waiting = False  # put variables to 0 so no if statements will run
            self.set = 0

            runs = sorted(self.data_dict.keys())
            pretty(self.main_dict)
            input_file = generate_input_file(self.input_file_path,
                                             self.main_dict,
                                             self.data_dict[runs[self.run-1]],
                                             1,
                                             len(self.data_dict.keys()))
            # Populate the massInfo dictionary based on the main_dict
            self.massInfo = populate_massInfo(self.main_dict, self.massInfo, False)
            # pretty(self.massInfo)
            # print 'END OF MASS INFO'
            # pretty(self.data_dict)

            # output = masscode_v1.MassCode(self.massInfo, self.data_dict)
            output = masscode_v2.MassCode(self.massInfo, self.data_dict)

            output_file = input_file[:].replace('.ntxt', '.nout')

            # Create the json file
            json_file_path = generate_json_file(self.input_file_path, self.main_dict, self.data_dict, output)
            print json_file_path

            # Run input file
            command = '"%s" "%s" "%s"\n' % (str(masscode_path), str(input_file), str(output_file))
            print command
            t = Thread(target=call, args=(command,))
            t.start()
            QApplication.restoreOverrideCursor()

            QTest.qWait(2000)
            self.window.close()

        try:
            row = self.main_dict['design matrix'][self.row_counter]  # becomes a row of the design matrix e.g. 1 -1 0 0
            set1 = [a + 1 for a, b in enumerate(row) if b == 1]  # set1 is all the weights with a 1 in the design matrix
            set2 = [a + 1 for a, b in enumerate(row) if
                    b == -1]  # set2 is all the weights with a -1 in the design matrix
        except IndexError:
            pretty(self.data_dict)

        if self.get_readout:
            # Get the measurement from the edit line
            self.readout = float(self.ui.readoutEdit.text())
            self.ui.readoutEdit.clear()

            self.update_history_table(self.readout, self.temp, self.press, self.humid)  # update the history table
            self.save_data()  # save the current readout and environmentals into the dictionary
            self.quicksave()  # save the latest info into the temp file

            self.get_readout = False
            self.ui.readoutEdit.setEnabled(0)

        if self.waiting:  # if a weight was just loaded, isMeasure will be True.
            self.ui.continueButton.setEnabled(0)  # disable the continue button

            self.stab_timer.start(1000)  # start the timer for the stabilization time countdown

            while not self.ui.readoutEdit.isEnabled():
                QTest.qWait(1000)

            self.ui.continueButton.setEnabled(1)

            if self.step == 4:  # at step 4, it enters the B2A2 phase
                self.AB = 2
            elif self.step == 8:  # at the end of B2A2, shift back into A1B1 mode and move to next row
                self.AB = 1
                self.row_counter += 1
                self.step = 0
                # Increment the progress bar
                self.ui.progressBar.setValue(self.row_counter)

            self.waiting = False
            self.get_readout = True
            self.step += 1

        elif self.set == 1:
            weights = []  # These are the weights that will be put on
            # Look at which weights need to be put on and display the weight names
            for weightNum in set1:
                weights.append(str(weightNum) + ' - ' + str(self.ui.reminderTable.item(weightNum-1, 0).text()))
            self.status_signal3.emit('Put on weight(s): %s \nPress Continue to begin stabilization time.' % weights)
            self.waiting = True
            if self.AB == 1:
                self.set = 2
            self.step += 1

        elif self.set == 2:
            weights = []  # same as above
            # same as above
            for weightNum in set2:
                weights.append(str(weightNum) + ' - ' + str(self.ui.reminderTable.item(weightNum-1, 0).text()))
            self.status_signal3.emit('Put on weight(s): %s \nPress Continue to begin stabilization time.' % weights)
            self.waiting = True
            if self.AB == 2:
                self.set = 1
            self.step += 1

    def status_slot3(self, args):
        """ Update the status browser with new argument """
        self.ui.statusBrowser3.clear()
        self.ui.statusBrowser3.append(args)

    def populate_reminder_table(self, cls):

        m = len(self.main_dict['design matrix'][0])
        self.ui.reminderTable.setRowCount(m)
        self.ui.reminderTable.setColumnCount(2)
        self.ui.reminderTable.setHorizontalHeaderLabels(["Weight", "Role"])

        for i in range(m):  # go row by row first
            for j in range(2):  # then go column by column
                if j == 0:
                    item = QtGui.QTableWidgetItem()
                    text = str(cls.ui.weightTable.item(i, j).text()).split('|')[
                        -1].strip()  # take the item from the main UI
                    item.setText(text)
                    self.ui.reminderTable.setItem(i, j, item)  # and copy it into this table
                else:
                    item = QtGui.QTableWidgetItem()
                    text = cls.ui.weightTable.cellWidget(i, j).currentText()
                    item.setText(text)
                    self.ui.reminderTable.setItem(i, j, item)

            # Set Row name
            item = QtGui.QTableWidgetItem()
            cls.ui.weightTable.setVerticalHeaderItem(i, item)
            item = cls.ui.weightTable.verticalHeaderItem(i)
            item.setText("Pos. %s" % (i + 1))

    def update_history_table(self, reading, temp, press, humid):
        # Has the last four measurements recorded
        measurement = QtGui.QTableWidgetItem(QtCore.QString(str(reading)))
        temperature = QtGui.QTableWidgetItem(QtCore.QString(str(temp)))
        pressure = QtGui.QTableWidgetItem(QtCore.QString(str(press)))
        humidity = QtGui.QTableWidgetItem(QtCore.QString(str(humid)))

        if self.ui.historyTable.rowCount() >= 4:
            # if there are four rows, clear the list
            #self.ui.historyTable.clearContents()
            for i in range(4):
                self.ui.historyTable.removeRow(0)

        row_num = self.ui.historyTable.rowCount()
        self.ui.historyTable.insertRow(row_num)  # Create a row at the bottom
        self.ui.historyTable.setItem(row_num, 0, measurement)
        self.ui.historyTable.setItem(row_num, 1, temperature)
        self.ui.historyTable.setItem(row_num, 2, pressure)
        self.ui.historyTable.setItem(row_num, 3, humidity)


    def click_ok(self):
        # Enter the stabilization time

        # Disable the stab time edit and the OK button
        self.ui.okButton.setEnabled(0)
        self.ui.stabEdit.setEnabled(0)

        # Clear the status Browser
        self.ui.statusBrowser3.clear()
        self.ui.statusBrowser3.append("Press continue.")

        # Enable the continue button
        self.ui.continueButton.setEnabled(1)

        # Read the stabEdit for the int
        self.stab_time = int(self.ui.stabEdit.text())

        if self.stab_time == '':
            self.stab_time = 35
        self.og_stab_time = self.stab_time

        # Open the save file dialog to save the tmp files, json files, and final input files
        # Prompt user for desired path
        file_dialog = QtGui.QFileDialog()
        self.input_file_path = QtGui.QFileDialog.getSaveFileName(file_dialog, 'Save as...',
                                                                 output_path + "\\" + datetime.date.today().strftime(
                                                                     "%Y%m%d")).replace('/', '\\')

    def save_data(self):
        # Get the latest temperatures
        self.press = self.db.latest_barometer_data(self.main_dict['barometer id'])[0]
        self.temp = self.db.latest_thermometer_data(self.main_dict['thermometer id'])[0]
        self.humid = self.db.latest_hygrometer_data(self.main_dict['hygrometer id'])[0]

        if self.step == 3:
            self.data_dict['run ' + str(self.run).zfill(2)]['observation ' + str(self.row_counter+1).zfill(2)]['1-A1'] \
                = [float(self.readout), float(self.temp), float(self.press), float(self.humid)]

        elif self.step == 5:
            self.data_dict['run ' + str(self.run).zfill(2)]['observation ' + str(self.row_counter+1).zfill(2)]['2-B1'] \
                = [float(self.readout), float(self.temp), float(self.press), float(self.humid)]

        elif self.step == 7:
            self.data_dict['run ' + str(self.run).zfill(2)]['observation ' + str(self.row_counter+1).zfill(2)]['3-B2'] \
                = [float(self.readout), float(self.temp), float(self.press), float(self.humid)]

        elif self.step == 1:
            self.data_dict['run ' + str(self.run).zfill(2)]['observation ' + str(self.row_counter).zfill(2)]['4-A2'] \
                = [float(self.readout), float(self.temp), float(self.press), float(self.humid)]

    def quicksave(self):
        # Saves the latest data into a .tmp file so if something goes wrong, parts of the run will still be there
        if os.path.isfile(self.input_file_path + '.tmp'):
            with open(self.input_file_path + '.tmp', 'a') as f:
                f.write('Reading: ' + str(self.readout) +
                        ' Temp: ' + str(self.temp) +
                        ' Press: ' + str(self.press) +
                        ' Humid: ' + str(self.humid) + '\n')
        else:
            with open(self.input_file_path + '.tmp', 'w+') as f:
                f.write('Calibration started ' + datetime.datetime.now().strftime('%m/%d/%Y %H:%M') + '\n')
                f.write('Reading: ' + str(self.readout) +
                        ' Temp: ' + str(self.temp) +
                        ' Press: ' + str(self.press) +
                        ' Humid: ' + str(self.humid) + '\n')
        f.close()

    def click_workdown(self):
        WorkdownUI(self.main_dict, self.massInfo)

    def cancel(self):
        quit_msg = "Are you sure you want to quit?"
        reply = QtGui.QMessageBox.question(self, 'Message:', quit_msg, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            QApplication.restoreOverrideCursor()
            self.window.close()
        else:
            pass

    def __exit__(self):
        self.window.close()
