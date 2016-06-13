__author__ = 'masslab'


from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtCore import QObject
from sub_ui.error_message import ErrorMessage
from populate_ui.populate_enviro_tree import populate_enviro_tree


class EditMetersUI(QObject):
    """
    Provides functionality to the UI that allows the user to add a weight to the database.
    This UI opens when the user clicks the button "Edit Weights" in the DB Access tab of the Main UI
    """

    def __init__(self, cls):
        """

        :param db: This is an instance of MainUI.db, allowing this class to access databaseORM.
        """
        self.db = cls.db

        self.dict = {'a': None,
                     'b': None,
                     'c': None,
                     'uncert': None,
                     'date': None}

        super(QObject, self).__init__()
        self.window = QtGui.QDialog(None, QtCore.Qt.WindowSystemMenuHint |
                                    QtCore.Qt.WindowTitleHint |
                                    QtCore.Qt.WindowMinMaxButtonsHint)
        self.window.setSizeGripEnabled(True)

        # Load the UI into self.ui
        self.ui = uic.loadUi('sub_ui/Edit_Meters.ui', self.window)

        # Populate the Enviro Tree
        populate_enviro_tree(cls, self)

        # Dictionary to set which widgets are enabled. Default only username/password
        self.widget_dict = {self.ui.usernameEdit: True,
                            self.ui.passwordEdit: True,
                            self.ui.loginButton: True,
                            self.ui.cancelButton: True,
                            self.ui.enviroTree: False,
                            self.ui.aEdit: False,
                            self.ui.bEdit: False,
                            self.ui.cEdit: False,
                            self.ui.uncertEdit: False,
                            self.ui.dateEdit: False,
                            self.ui.applyButton: False}

        # Actually enable/disable the widgets
        self.update_widgets()

        # Set up the event handlers
        self.callback_connector()

        # Execute the ui
        self.window.exec_()

    def callback_connector(self):
        self.ui.loginButton.clicked.connect(self.handle_login)
        self.ui.cancelButton.clicked.connect(self.__exit__)
        self.ui.applyButton.clicked.connect(self.apply_changes)

    def handle_login(self):
        identifier = self.db.check_user_password(self.ui.usernameEdit.text(), self.ui.passwordEdit.text())
        # if the username and password are found in the database, allow the user to edit the other widgets
        if identifier:
            self.widget_dict = {self.ui.usernameEdit: False,
                                self.ui.passwordEdit: False,
                                self.ui.loginButton: False,
                                self.ui.cancelButton: False,
                                self.ui.enviroTree: True,
                                self.ui.aEdit: True,
                                self.ui.bEdit: True,
                                self.ui.cEdit: True,
                                self.ui.uncertEdit: True,
                                self.ui.dateEdit: True,
                                self.ui.applyButton: True}
            self.update_widgets()
        # if the user/pass aren't found,
        else:
            ErrorMessage('Login Failed')

    def apply_changes(self):
        self.dict['a'] = self.ui.aEdit.text()
        self.dict['b'] = self.ui.bEdit.text()
        self.dict['c'] = self.ui.cEdit.text()
        self.dict['uncert'] = self.ui.uncertEdit.text()
        self.dict['date'] = self.ui.dateEdit.text()

        probe = self.ui.enviroTree.currentItem().text(0).split('|')[1]
        self.db.update_machines(self.ui.enviroTree.currentItem().parent().text(0),
                                probe,
                                self.dict)

        self.window.close()

    def update_widgets(self):
        for value, key in self.widget_dict.items():
            value.setEnabled(key)

    def __exit__(self):
        self.window.close()