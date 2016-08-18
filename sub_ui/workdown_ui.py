__author__ = 'masslab'

import json
from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtCore import QObject
from config import base_path


class WorkdownUI(QObject):
    """
    Allows the user to enter the restraint, check, and report vector for the workdown or workup.
    Usually used when there are repeated restraint/check vectors: i.e. restraint = [0,0,0,1,1], check = [0,0,0,1,-1]

    """

    def __init__(self, main_dict, mass_info):
        """

        :param main_dict: This is an instance of MainUI's main dictionary, allowing this class to access the entries
        :param mass_info: This is an instance of the massInfo dict so that the workdown stuff can be entered
        """

        self.main_dict = main_dict
        self.massInfo = mass_info

        super(QObject, self).__init__()
        self.window = QtGui.QDialog(None, QtCore.Qt.WindowSystemMenuHint |
                                    QtCore.Qt.WindowTitleHint |
                                    QtCore.Qt.WindowMinMaxButtonsHint)
        self.window.setSizeGripEnabled(True)

        # Load the UI into self.ui
        self.ui = uic.loadUi('sub_ui/WorkdownUI.ui', self.window)

        # Set up the event handlers
        self.callback_connector()

        # Execute the ui
        self.window.exec_()

    def callback_connector(self):
        self.ui.selectParentButton.clicked.connect(self.click_select_parent)
        self.ui.okButton.clicked.connect(self.click_ok)

    def click_select_parent(self):

        file_dialog = QtGui.QFileDialog()
        file_name = QtGui.QFileDialog.getOpenFileName(file_dialog, "Select the PREVIOUS output file", base_path,
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

    def click_ok(self):
        try:
            # Try splitting by commas
            self.main_dict['restraint vec'] = [int(i) for i in str(self.ui.restraintVecEdit.text()).split(',')]
            self.main_dict['check vec'] = [int(i) for i in str(self.ui.checkVecEdit.text()).split(',')]
            self.main_dict['report vec'] = [int(i) for i in str(self.ui.reportVecEdit.text()).split(',')]

        except ValueError:
            # Split by spaces otherwise
            self.main_dict['restraint vec'] = [int(i) for i in str(self.ui.restraintVecEdit.text()).split()]
            self.main_dict['check vec'] = [int(i) for i in str(self.ui.checkVecEdit.text()).split()]
            self.main_dict['report vec'] = [int(i) for i in str(self.ui.reportVecEdit.text()).split()]
        print self.main_dict['restraint vec'], self.main_dict['check vec']

        self.__exit__()

    def __exit__(self):
        self.window.close()
