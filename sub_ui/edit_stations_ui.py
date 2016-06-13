__author__ = 'masslab'


from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtCore import QObject


class EditStationUI(QObject):
    """
    Provides functionality to the UI that allows the user to edit which environmentals are associated with
    a particular balance.
    """

    def __init__(self, db):
        """

        :param db: This is an instance of MainUI.db, allowing this class to access databaseORM
        """
        self.db = db

        self.dict = {'balance_id': None,
                     'thermometer_id': None,
                     'barometer_id': None,
                     'hygrometer_id': None}

        super(QObject, self).__init__()
        self.window = QtGui.QDialog(None, QtCore.Qt.WindowSystemMenuHint |
                                    QtCore.Qt.WindowTitleHint |
                                    QtCore.Qt.WindowMinMaxButtonsHint)
        self.window.setSizeGripEnabled(True)

        # Load the UI into self.ui
        self.ui = uic.loadUi('sub_ui/Edit_Stations.ui', self.window)

        # Populate the combo boxes: balances, thermometers, barometers, and hygrometers
        balances = self.db.get_balance_names()
        thermometers = self.db.get_thermometers()
        barometers = self.db.get_barometers()
        hygrometers = self.db.get_hygrometers()
        self.ui.balanceCombo.clear()
        self.ui.balanceCombo.addItems(balances)
        self.ui.thermometerCombo.clear()
        self.ui.thermometerCombo.addItems(thermometers)
        self.ui.barometerCombo.clear()
        self.ui.barometerCombo.addItems(barometers)
        self.ui.hygrometerCombo.clear()
        self.ui.hygrometerCombo.addItems(hygrometers)

        # Set up the event handlers
        self.ui.applyButton.clicked.connect(self.apply_changes)

        # Execute the ui
        self.window.exec_()

    def apply_changes(self):
        self.dict['balance_id'] = self.ui.balanceCombo.currentText().split('|')[0]
        self.dict['thermometer_id'] = self.ui.thermometerCombo.currentText().split('|')[0]
        self.dict['barometer_id'] = self.ui.barometerCombo.currentText().split('|')[0]
        self.dict['hygrometer_id'] = self.ui.hygrometerCombo.currentText().split('|')[0]

        self.db.update_stations(self.dict)

        self.window.close()

    def __exit__(self):
        self.window.close()