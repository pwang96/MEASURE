__author__ = 'masslab'

import sys
import re
import os
import json
from threading import Thread
from Queue import Queue
from PyQt4 import QtGui, uic
from PyQt4.QtCore import QObject, pyqtSignal
from utility.run_masscode_queue import run_old_masscode
from utility.show_dictionary import pretty
from config import base_path, output_path, package_path
from config import software_name
from sub_ui.comparator_ui import ComparatorUi
from sub_ui.error_message import ErrorMessage
from sub_ui.login import LoginUi
from populate_ui import PopulateUI
from populate_dictionary import populate_dictionary
from plots.control_chart import ControlChart
from plots.Environmentals import Environmentals
from plots.fileplot_environment import FileEnvironmentPlot
from plots.fileplot_mass import FileMassPlot
from populate_ui.populate_db_access import populate_db_access
from sub_ui.add_weight_ui import AddWeightUI
from sub_ui.edit_meters_ui import EditMetersUI
from sub_ui.manual_balance_ui import ManualBalanceUI
from sub_ui.edit_stations_ui import EditStationUI
from sub_ui.add_station_ui import AddStationUI
from sub_ui.custom_design_matrix import CustomDesignUI
from sub_ui.edit_existing_weight_ui import EditExistingWeightUI
from sub_ui.manual_ui import ManualUI
from sub_ui.air_density_calc_ui import AirDensityCalc
from sqlalchemy.exc import OperationalError
from utility.parse_send import parse_output, send_output
from utility.ntxt_to_MassCode2 import convert_masscode
from file_generators.generate_output_file import generate_output_file
# ------------------------------------------------------------------------------------------------------


try:
    _encoding = QtGui.QApplication.UnicodeUTF8

    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class MainUI(QObject):
    """ Provides functionality for the main user interface

    The main functionality available in this user interface is balance, weighing design, and weight selection for
    a potential mass calibration.  Additional functionality includes "masscode" input file processing,
    "masscode" output file parsing and graphing, and mass station manipulation.

    The user interface object structure is loaded from the QT Designer xml file 'main.ui' using the PyQt4.uic module.
    MainUI creates an instance of the DatabaseORM class, which is used to fetch data from the calibration database.
    Information on the database populates various menus in the user interface and ultimately stores the
    mass calibration data for easy manipulation.  The DatabaseORM instance is passed to the comparator sub-ui

    The dictionary main_dict collects all metadata necessary to process a mass calibration.  This dictionary
    is passed to the comparator sub-ui.

    Args:
       window(QtGui object):  the parent object which the user interface inherits
    """

    # Initialize main dictionary
    main_dict = {'design id': None,
                 'design name': '',
                 'design matrix': [],
                 'balance id': None,
                 'balance name': None,
                 'balance std dev': None,
                 'balance port': None,
                 'balance serial settings': [],
                 'station id': None,
                 'thermometer id': None,
                 'temperature coeff': None,
                 'temperature uncert': None,
                 'barometer id': None,
                 'pressure coeff': None,
                 'pressure uncert': None,
                 'hygrometer id': None,
                 'humidity coeff': None,
                 'humidity uncert': None,
                 'restraint vec': [],
                 'check vec': [],
                 'report vec': [],
                 'next restraint vec': [],
                 'addon info': [],
                 'addon history id': [],
                 'weight info': [],
                 'weight history id': [],
                 'weight internal': [],
                 'weight type b': [],
                 'weight between': [],
                 'weight density uncert': [],
                 'cg differences': [],
                 'restraint uncert': None,  # Only type B if not a workdown, [type A, type B] if it is a workdown
                 'check between': None,
                 'units': None,
                 'user id': None,
                 #------------------------------------------------
                 'index': None}  # for the environmental plot, list of name and serial of environmental machines
                 #------------------------------------------------

    quit_signal = pyqtSignal(int)

    def __init__(self, window):
        super(QObject, self).__init__()
        window.setWindowIcon(QtGui.QIcon('Masses.png'))
        window.setWindowTitle(software_name)
        
        self.ui = uic.loadUi(r'L:\internal\684.07\Mass_Project\Software\PythonProjects\measure\main.ui', window)

        self.quit_signal.connect(self.quit_slot)

        # Instantiate the database object relational mapping with login()
        self.db = None
        self.login()

        # Populate the menus within the main UI via the database
        self.populate_ui = PopulateUI(self)     # CALIBRATION TAB: Populates the balance combo box, weight list, enviro list
                                                # MANUAL BALANCE TAB: Also populates the balance combo box, design list,
                                                # weight list in the manual balance tab

        self.input_file_queue = Queue()
        self.json_file_queue = Queue()

        # Temporary testing config
        self.ui.balNameCombo.setCurrentIndex(0)
        self.ui.chooseEnviroCombo.setCurrentIndex(0)

        # Activate the event handlers
        self.callback_connector()

        # Display the main UI
        window.show()

    def quit_slot(self):
        # Slot for quit_signal
        app.quit()

    def callback_connector(self):
        """ Activate event detection"""
        # CALIBRATION TAB
        self.ui.balNameCombo.activated.connect(self.activate_balance)
        self.ui.designCombo.activated.connect(self.activate_design)
        self.ui.removeButton.clicked.connect(self.remove_item)
        self.ui.configBalButton.clicked.connect(self.click_config_bal)  # Automatic Balance
        self.ui.configManBalButton.clicked.connect(self.click_configure_manual)  # Manual Balance
        self.ui.manualButton.clicked.connect(self.click_manual)  # manually enter the readings

        # MASS CODE TAB
        self.ui.masscodeButton.clicked.connect(self.click_masscode)
        self.ui.oldMasscodeButton.clicked.connect(self.click_old_masscode)
        self.ui.inputButton.clicked.connect(self.click_input)
        self.ui.massCodeRemoveButton.clicked.connect(self.click_masscode_remove)

        # BEAUTIFY JSON TAB
        self.ui.selectFilesButton.clicked.connect(self.click_select_files)
        self.ui.beautifyButton.clicked.connect(self.beautify_json)
        self.ui.beautifyRemoveButton.clicked.connect(self.click_beautify_remove)

        # PLOT TAB
        self.ui.outputBrowseButton.clicked.connect(self.click_browse)  # Plot Tab, Browsing Output files
        self.ui.extractButton.clicked.connect(self.extract_data)
        self.ui.outputList.itemActivated.connect(self.extract_data)
        self.ui.sendButton.clicked.connect(self.send_data)
        self.ui.controlChartRadio.toggled.connect(self.checked_control_chart)  # Control Chart
        self.ui.weightList.itemActivated.connect(self.draw_control_chart)
        self.ui.chooseEnviroCombo.activated.connect(self.get_apparati)  # Environmentals
        self.ui.enviroList.itemActivated.connect(self.draw_environmentals)

        # DB ACCESS TAB
        self.ui.balanceRadio.toggled.connect(self.checked_balances)
        self.ui.stationRadio.toggled.connect(self.checked_stations)
        self.ui.externalWeightRadio.toggled.connect(self.checked_external_weights)
        self.ui.thermometerRadio.toggled.connect(self.checked_thermometers)
        self.ui.hygrometerRadio.toggled.connect(self.checked_hygrometers)
        self.ui.barometerRadio.toggled.connect(self.checked_barometers)
        self.ui.addStationButton.clicked.connect(self.click_add_stations)
        self.ui.editStationButton.clicked.connect(self.click_edit_stations)
        self.ui.editWeightButton.clicked.connect(self.click_edit_weights)
        self.ui.editMachinesButton.clicked.connect(self.click_edit_machines)
        self.ui.editExistingWeightButton.clicked.connect(self.click_edit_existing_weight)

        # MISC TAB
        self.ui.airDensitySolverButton.clicked.connect(self.click_air_density_solver)

# -------------------------------------------------------------------------------------------------------------------------
        app.aboutToQuit.connect(self.exit_function)

    def widget_handler(self, arg):
        """ Enable or disable widgets in main ui as specified in list arg"""
        self.ui.balNameCombo.setEnabled(arg[0])
        self.ui.designCombo.setEnabled(arg[1])
        self.ui.weightTable.setEnabled(arg[2])
        self.ui.configBalButton.setEnabled(arg[3])
        self.ui.masscodeButton.setEnabled(arg[4])

    def login(self):
        """ Prompt user for database credentials """

        # Execute login user interface
        login = LoginUi(self.quit_signal)
        self.db = login.db
        self.main_dict['user id'] = login.ident
        # If the login is cancelled, raise an error to properly quit
        if login.ident is None:
            raise RuntimeError('Login cancelled')
            app.quit()

# -------------------------------------------------------------------------------------------------------------------------
    def remove_item(self):
        """ Slot for removeButton.clicked
        Clears the selected item in the weight table (calibration tab)
        :return: None
        """
        current_item = self.ui.weightTable.currentItem()
        current_item.setText('')

    def click_browse(self):
        """ Slot for outputBrowseButton.clicked
        Opens a browser to look for files to parse and graph (plot tab)
        :return: None
        """
        file_dialog = QtGui.QFileDialog()
        file_names = QtGui.QFileDialog.getOpenFileNames(file_dialog, "Select masscode files to plot",
                                                        output_path, "Output files (*.json *.nout *.txt)")
        self.ui.outputList.addItems(file_names)

    def click_select_files(self):
        """
        Opens a browser to look for json files to create output files from (beautify json tab)
        :return: None
        """
        file_dialog = QtGui.QFileDialog()
        file_names = QtGui.QFileDialog.getOpenFileNames(file_dialog, "Select json files to beautify",
                                                        output_path, "Output files (*.json)")
        self.ui.jsonList.addItems(file_names)

    def click_beautify_remove(self):
        """
        Removes the selected json files in the jsonList (beautify json tab)
        :return: None
        """
        for item in self.ui.jsonList.selectedItems():
            self.ui.jsonList.takeItem(self.ui.jsonList.row(item))

    def beautify_json(self):
        """ Push input files in ui.jsonList through the masscode (multi-threaded) """
        self.ui.statusBrowser.clear()
        for n in range(self.ui.jsonList.count()):
            self.json_file_queue.put(str(self.ui.jsonList.item(n).text()))

        for n in range(self.ui.jsonList.count()):
            beautify_t = Thread(target=generate_output_file, args=(self.json_file_queue.get(),))
            beautify_t.start()
        self.ui.jsonList.clear()
        self.ui.statusBrowser.append("Task complete!")
        self.ui.inputList.clear()

    def checked_control_chart(self):
        """Populates the list of weights whose history can be graphed"""
        weight_list = self.db.get_all_weights()
        self.ui.weightList.clear()
        self.ui.weightList.addItems(weight_list)

    def draw_control_chart(self):
        """Creates an instance of ControlChart (matplotlib QTagg), graphs it in the PLOT tab """
        weight_name = self.ui.weightList.currentItem().text()
        self.controlChart = ControlChart(self, weight_name)
        self.ui.plotArea.addSubWindow(self.controlChart).setWindowTitle("Control Chart")
        self.controlChart.show()

    def get_apparati(self):
        """After the user selects which environmental data to plot, populate the list with the different apparati"""
        (apparatus_names, apparatus_ids, apparatus_serial) = self.db.get_apparati(self.ui.chooseEnviroCombo.currentText())
        name_and_serial = [str(a)+ ' ' + str(b) for a, b in zip(apparatus_names, apparatus_serial)]
        self.main_dict['index'] = dict(zip(name_and_serial, apparatus_ids))
        self.ui.enviroList.clear()
        self.ui.enviroList.addItems([str(a)+', serial: '+str(b) for a, b in zip(apparatus_names, apparatus_serial)])

    def draw_environmentals(self):
        """ Draws the environmental data, look in plots/Environmentals.py"""
        apparatus_name = self.ui.enviroList.currentItem().text()
        regex = r'(.*), serial: (\w*)'
        apparatus_name = str(re.findall(regex, apparatus_name)[0][0])
        apparatus_serial = str(re.findall(regex, apparatus_name)[0][1])
        apparatus_id = self.main_dict['index'][str(apparatus_name)+' '+str(apparatus_serial)]
        environment_type = self.ui.chooseEnviroCombo.currentText()
        self.environmentals = Environmentals(self, environment_type, apparatus_name, apparatus_id, apparatus_serial)
        self.ui.plotArea.addSubWindow(self.environmentals).setWindowTitle("%s Graph" % (environment_type))
        self.environmentals.show()

    def checked_stations(self):
        # Populates the DB table with all stations
        populate_db_access(self, 'stations')

    def checked_balances(self):
        # Populates the DB table with all balances
        populate_db_access(self, 'balances')

    def checked_external_weights(self):
        # Populates the DB table with all external weights
        populate_db_access(self, 'weights_external')

    def checked_thermometers(self):
        # Populates the DB table with all thermometers
        populate_db_access(self, 'thermometers')

    def checked_hygrometers(self):
        # Populates the DB table with all hygrometers
        populate_db_access(self, 'hygrometers')

    def checked_barometers(self):
        # Populates the DB table with all barometers
        populate_db_access(self, 'barometers')

    def click_add_stations(self):
        # Brings up the UI to add a station
        AddStationUI(self.db)

    def click_edit_stations(self):
        # Brings up the UI to edit a station
        EditStationUI(self.db)

    def click_edit_weights(self):
        # Brings up the UI to add an external weight
        AddWeightUI(self)

    def click_edit_machines(self):
        # Brings up the UI to edit an environmental machine
        EditMetersUI(self)

    def click_edit_existing_weight(self):
        # Brings up the UI to edit an existing weight
        EditExistingWeightUI(self)

    def click_configure_manual(self):
        # Brings up the UI to conduct a calibration with a manual balance
        try:
            # Populate the dictionary
            populate_dictionary(self)
            pretty(self.main_dict)

            # Call the Manual Balance UI
            ManualBalanceUI(self)

        except IndexError:
            ErrorMessage('Please fill in all the weights!')

    def click_manual(self):
        # Brings up the manual UI. This UI allows users to manually enter the readings
        # while automatically getting the environmental readings
        try:
            # Populate the main_dict
            populate_dictionary(self)
            pretty(self.main_dict)

            # Display Manual UI
            ManualUI(self)

        except IndexError:
            ErrorMessage("Please fill in all the weights!")

    def extract_data(self):
        # gets the environmental and mass data from an output file and graphs it
        try:
            filename = self.ui.outputList.currentItem().text()
        except AttributeError:
            ErrorMessage("No file selected!")

        # Check if type is json or nout
        if 'nout' in filename:
            with open(filename) as f:
                text = f.readlines()
                title = os.path.basename(str(f.name))
            self.fileplot = FileEnvironmentPlot(text, 'nout')
        elif 'json' in filename:
            with open(filename) as f:
                data = json.load(f)
                title = os.path.basename(str(f.name))
            self.fileplot = FileEnvironmentPlot(data, 'json')
        self.ui.plotArea.addSubWindow(self.fileplot).setWindowTitle("Environments Graph for %s" % title)
        self.fileplot.show()

    def send_data(self):
        # parses the output file and sends the weight data to the database.
        # gets the date, Balance ID, Weight IDs, measurements

        count = self.ui.outputList.count()
        for i in range(count):

            filename = self.ui.outputList.item(i).text()

            try:
                data = parse_output(filename)
                r, c, u1, u2 = send_output(data, self.db)
                self.ui.statusBrowser.append('Data uploaded to database!')
                # self.ui.outputList.takeItem(i)
            except AssertionError:
                ErrorMessage("Not an output file! Make sure the file ends with '.nout'.")
        self.ui.outputList.clear()
        try:
            self.massplot = FileMassPlot(self.db, r, c, u1, u2)
            self.ui.plotArea.addSubWindow(self.massplot).setWindowTitle("Mass control charts")
            self.massplot.show()
        except UnboundLocalError:
            pass

# -------------------------------------------------------------------------------------------------------------------------

    def click_config_bal(self):
        """ Populate main_dict with selected items and call the comparator user interface """
        try:
            # Populate and show main dictionary
            populate_dictionary(self)
            pretty(self.main_dict)  # prints out the main dictionary

            # Initializes the balance ui class stored in the balance dict under the balance id in the main dict
            ComparatorUi(self.main_dict, self.db)
        except IndexError:
            ErrorMessage('Please fill in all the weights!')

    def activate_balance(self):
        """ Newly selected balance is used to populate main_dict and weighing design menu """
        # Reset the design combo box and weight table
        self.ui.designCombo.clear()
        self.ui.weightTable.setRowCount(0)
        self.main_dict['balance id'] = int(self.ui.balNameCombo.currentText().split(" | ")[0])
        self.main_dict['balance serial settings'] = list(self.db.get_serial_settings(self.main_dict['balance id']))
        [name, std] = self.db.balance_data(self.main_dict['balance id'])
        self.main_dict['balance name'] = name
        self.main_dict['balance std dev'] = float(std)

        # Populate design menu with designs compatible with selected balance
        self.populate_ui.design_menu(self)

        # Find the station id using the balance id and set the station combo
        [self.main_dict['station id'],
         self.main_dict['thermometer id'],
         self.main_dict['barometer id'],
         self.main_dict['hygrometer id']] = self.db.station_id(self.main_dict['balance id'])
        try:
            self.update_environment_table()
        except OperationalError:
            ErrorMessage('No/wrong environmentals associated with balance!')
        except IndexError:
            ErrorMessage('Invalid Environmentals')

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

    def activate_design(self):
        """ Populate main_dict with selected design and initialize the weight table with appropriate number of rows """
        # Transfer the design info into the dictionary

        if 'Custom' in self.ui.designCombo.currentText().split("|")[1]:  # if a custom is chosen, pull up the UI
            CustomDesignUI(self.db)  # the UI will update the database so the next part of the code will work

        [self.main_dict['design id'],
         self.main_dict['design name'],
         array] = self.db.design_data(int(self.ui.designCombo.currentText().split("|")[0]))

        # Display design name in the status browser
        self.ui.statusBrowser.clear()
        self.ui.statusBrowser.append('Design: ' + self.main_dict['design name'])

        # Collect design into array and display in status browser
        self.main_dict['design matrix'] = []
        try:
            for row in array.split(' ; '):
                self.main_dict['design matrix'].append([int(a) for a in row.split(' ')])
                self.ui.statusBrowser.append(row)
        except ValueError:
            for row in array.split('; '):
                self.main_dict['design matrix'].append([int(a) for a in row.split(' ')])
                self.ui.statusBrowser.append(row)

        # Populate the weight table based on chosen design
        self.populate_ui.table_widget(self)

    def click_input(self):
        """ Prompt user to select input files to be added to the input file list """
        file_dialog = QtGui.QFileDialog()
        file_names = QtGui.QFileDialog.getOpenFileNames(file_dialog,
                                                        "Select masscode input files", output_path, "(*.ntxt *.txt)")
        self.ui.inputList.addItems(file_names)
        self.ui.masscodeButton.setEnabled(True)

    def click_masscode(self):
        """ Push input files in ui.inputList through the masscode (multi-threaded) """
        self.ui.masscodeButton.setEnabled(False)
        self.ui.statusBrowser.clear()
        for n in range(self.ui.inputList.count()):
            self.input_file_queue.put(str(self.ui.inputList.item(n).text()))

        for n in range(self.ui.inputList.count()):

            masscode_t = Thread(target=convert_masscode, args=(self.input_file_queue.get(),))
            masscode_t.start()

        self.ui.statusBrowser.append("Task complete!")
        self.ui.inputList.clear()

    def click_old_masscode(self):
        """
        Runs the files through the old Fortran masscode by using subprocess.call
        :return: None
        """
        for n in range(self.ui.inputList.count()):
            input_path = str(self.ui.inputList.item(n).text())

            output_path = input_path.replace('.ntxt', '.nout')
            print repr(input_path), '\n', repr(output_path)
            try:
                run_old_masscode(input_path, output_path)
                # Doesn't work through threading for some reason, see utility/run_old_masscode.py, which works
            except:
                ErrorMessage("Something Happened")

        self.ui.statusBrowser.append("Task Complete!")
        self.ui.inputList.clear()

    def click_masscode_remove(self):
        # Removes the selected items in the input list
        for item in self.ui.inputList.selectedItems():
            self.ui.inputList.takeItem(self.ui.inputList.row(item))

    def click_air_density_solver(self):
        AirDensityCalc()

    @staticmethod
    def exit_function():
        app.quit()




if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    app.setStyle("cleanlooks")
    main_window = QtGui.QMainWindow()
    main_ui = MainUI(main_window)
    sys.exit(app.exec_())
