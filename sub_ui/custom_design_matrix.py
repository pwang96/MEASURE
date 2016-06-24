__author__ = 'masslab'


from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtCore import QObject


class CustomDesignUI(QObject):
    """
    Provides functionality to the UI that allows the user to add a weight to the database.
    This UI opens when the user clicks the button "Edit Weights" in the DB Access tab of the Main UI
    """

    def __init__(self, db):
        """

        :param db: This is an instance of MainUI.db, allowing this class to access databaseORM
        """
        self.db = db

        super(QObject, self).__init__()
        self.window = QtGui.QDialog(None, QtCore.Qt.WindowSystemMenuHint |
                                    QtCore.Qt.WindowTitleHint |
                                    QtCore.Qt.WindowMinMaxButtonsHint)
        self.window.setSizeGripEnabled(True)

        # Load the UI into self.ui
        self.ui = uic.loadUi('sub_ui/Custom_Design_Matrix.ui', self.window)

        # Set up the event handlers
        self.callback_connector()

        # Start out with done button disabled
        self.ui.doneButton.setEnabled(0)

        # Execute the ui
        self.window.exec_()

    def callback_connector(self):
        self.ui.checkBox.stateChanged.connect(self.checked)
        self.ui.doneButton.clicked.connect(self.click_done)

    def checked(self):
        # Disable the done button unless they have double checked!
        if self.ui.checkBox.isChecked():
            self.ui.doneButton.setEnabled(1)
        else:
            self.ui.doneButton.setEnabled(0)

    def click_done(self):
        # sends the text to the database
        text = self.ui.designEdit.toPlainText()
        text = str(text).replace('\n', ' ')
        self.db.add_custom_design(text)

        self.window.close()

    def __exit__(self):
        self.window.close()