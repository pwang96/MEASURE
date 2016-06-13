__author__ = 'masslab'

import sys
import re
from threading import Thread
from Queue import Queue
from PyQt4 import QtGui, uic
from PyQt4.QtCore import QObject, pyqtSignal
from utility.database_orm import DatabaseORM
from utility.run_masscode_queue import run_masscode_queue
from utility.show_dictionary import pretty
from config import base_path
from config import software_name
from sub_ui.comparator_ui import ComparatorUi
from sub_ui.error_message import ErrorMessage
from sub_ui.login import LoginUi
from populate_ui import PopulateUI
from populate_dictionary import populate_dictionary
# ------------------------------------------------------------------------------------------------------
from plots.control_chart import ControlChart
from plots.Environmentals import Environmentals
from populate_ui.populate_db_access import populate_db_access
from sub_ui.add_weight_ui import AddWeightUI
from sub_ui.edit_meters_ui import EditMetersUI
from sub_ui.manual_balance_ui import ManualBalanceUI
from sub_ui.edit_stations_ui import EditStationUI
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
                 'restraint type b': None,
                 'check between': None,
                 'units': None,
                 'user id': None,
                 #------------------------------------------------
                 'index': None}
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
        self.populate_ui = PopulateUI(self)  # CALIBRATION TAB: Populates the balance combo box, weight list, enviro list
                                             # MANUAL BALANCE TAB: Also populates the balance combo box, design list,
                                             # weight list in the manual balance tab

        self.input_file_queue = Queue()


        # Temporary testing config
        self.ui.balNameCombo.setCurrentIndex(2)
        self.ui.chooseEnviroCombo.setCurrentIndex(0)

        # Activate the event handlers
        self.callback_connector()

        # Display the main UI
        window.show()

    def quit_slot(self):
        app.quit()

    def callback_connector(self):
        """ Activate event detection"""
        self.ui.balNameCombo.activated.connect(self.activate_balance)
        self.ui.designCombo.activated.connect(self.activate_design)
        self.ui.inputButton.clicked.connect(self.click_input)
        self.ui.masscodeButton.clicked.connect(self.click_masscode)
        self.ui.configBalButton.clicked.connect(self.click_config_bal)

# -------------------------------------------------------------------------------------------------------------------------

        self.ui.outputBrowseButton.clicked.connect(self.click_browse)  # Browsing Output files

        self.ui.controlChartRadio.toggled.connect(self.checked_control_chart)  # Control Chart
        self.ui.weightList.itemActivated.connect(self.draw_control_chart)

        self.ui.chooseEnviroCombo.activated.connect(self.get_apparati)  # Environmentals
        self.ui.enviroList.itemActivated.connect(self.draw_environmentals)

        self.ui.balanceRadio.toggled.connect(self.checked_balances)  # Database access
        self.ui.stationRadio.toggled.connect(self.checked_stations)
        self.ui.externalWeightRadio.toggled.connect(self.checked_external_weights)
        self.ui.thermometerRadio.toggled.connect(self.checked_thermometers)
        self.ui.hygrometerRadio.toggled.connect(self.checked_hygrometers)
        self.ui.barometerRadio.toggled.connect(self.checked_barometers)
        self.ui.addStationButton.clicked.connect(self.click_add_stations)
        self.ui.editStationButton.clicked.connect(self.click_edit_stations)
        self.ui.editWeightButton.clicked.connect(self.click_edit_weights)
        self.ui.editMachinesButton.clicked.connect(self.click_edit_machines)

        self.ui.configManBalButton.clicked.connect(self.click_manual_go)  # Manual Balance

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
        if login.ident == None:
            app.quit()

# -------------------------------------------------------------------------------------------------------------------------
    def click_browse(self):
        """ Opens a browser to look for files to parse and graph"""
        file_dialog = QtGui.QFileDialog()
        file_names = QtGui.QFileDialog.getOpenFileNames(file_dialog, "Select masscode files to plot", base_path, "*.ntxt")
        self.ui.outputList.addItems(file_names)

    def checked_control_chart(self):
        """Populates the list of weights whose history can be graphed"""
        weight_list = self.db.get_all_weights()
        self.ui.weightList.clear()
        self.ui.weightList.addItems(weight_list)

    def draw_control_chart(self):
        """ """
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
        apparatus_name, apparatus_serial = str(re.findall(regex, apparatus_name)[0][0]), str(re.findall(regex, apparatus_name)[0][1])
        apparatus_id = self.main_dict['index'][str(apparatus_name)+' '+str(apparatus_serial)]
        environment_type = self.ui.chooseEnviroCombo.currentText()
        self.environmentals = Environmentals(self, environment_type, apparatus_name, apparatus_id, apparatus_serial)
        self.ui.plotArea.addSubWindow(self.environmentals).setWindowTitle("%s Graph" % (environment_type))
        self.environmentals.show()

    def checked_stations(self):
        populate_db_access(self, 'stations')

    def checked_balances(self):
        populate_db_access(self, 'balances')

    def checked_external_weights(self):
        populate_db_access(self, 'weights_external')

    def checked_thermometers(self):
        populate_db_access(self, 'thermometers')

    def checked_hygrometers(self):
        populate_db_access(self, 'hygrometers')

    def checked_barometers(self):
        populate_db_access(self, 'barometers')

    def click_add_stations(self):
        pass

    def click_edit_stations(self):
        EditStationUI(self.db)

    def click_edit_weights(self):
        AddWeightUI(self.db)

    def click_edit_machines(self):
        EditMetersUI(self)

    def click_manual_go(self):
        ManualBalanceUI(self.main_dict, self.db)
# -------------------------------------------------------------------------------------------------------------------------

    def click_config_bal(self):
        """ Populate main_dict with selected items and call the comparator user interface """
        # Populate and show main dictionary
        populate_dictionary(self)
        pretty(self.main_dict)

        # TEMPORARY CODE, saves main dictionary for debugging purposes
        # ---------------------------------------------------------
        # with open('SubUIs/main_dict.json', 'w+') as fp:
        #     json.dump(self.main_dict, fp)
        # ---------------------------------------------------------

        # Initializes the balance ui class stored in the balance dict under the balance id in the main dict
        ComparatorUi(self.main_dict, self.db)

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
        self.update_environment_table()

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
        [self.main_dict['design id'],
         self.main_dict['design name'],
         array] = self.db.design_data(int(self.ui.designCombo.currentText().split("|")[0]))

        # Display design name in the status browser
        self.ui.statusBrowser.clear()
        self.ui.statusBrowser.append('Design: ' + self.main_dict['design name'])

        # Collect design into array and display in status browser
        self.main_dict['design matrix'] = []
        for row in array.split(' ; '):
            self.main_dict['design matrix'].append([int(a) for a in row.split(' ')])
            self.ui.statusBrowser.append(row)

        # Populate the weight table based on chosen design
        self.populate_ui.table_widget(self)

    def click_input(self):
        """ Prompt user to select input files to be added to the input file list """
        file_dialog = QtGui.QFileDialog()
        file_names = QtGui.QFileDialog.getOpenFileNames(file_dialog, "Select masscode input files", base_path, "*.ntxt")
        self.ui.inputList.addItems(file_names)
        self.ui.masscodeButton.setEnabled(True)

    def click_masscode(self):
        """ Push input files in ui.inputList through the masscode (multi-threaded) """
        self.ui.masscodeButton.setEnabled(False)
        self.ui.statusBrowser.clear()
        for n in range(self.ui.inputList.count()):
            print self.ui.inputList.item(n).text()
            self.input_file_queue.put(str(self.ui.inputList.item(n).text()))
        for n in range(5):
            masscode_t = Thread(target=run_masscode_queue, args=(self,))
            masscode_t.start()
        self.ui.statusBrowser.append("Task complete!")

    @staticmethod
    def exit_function():
        app.quit()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    app.setStyle("cleanlooks")
    main_window = QtGui.QMainWindow()
    main_ui = MainUI(main_window)
    sys.exit(app.exec_())
