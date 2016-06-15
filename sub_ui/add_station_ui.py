__author__ = 'masslab'


from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtCore import QObject


class AddStationUI(QObject):
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
        self.ui = uic.loadUi('sub_ui/Add_Station.ui', self.window)

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
        self.callback_connector()

        # Initialize the dictionary that holds the weight's attributes
        self.dict = {"balance_id": None,
                     "thermometer_id": None,
                     "barometer_id": None,
                     "hygrometer_id": None,
                     "name":None,
                     "building":None,
                     "room": None}

        # Execute the ui
        self.window.exec_()

    def callback_connector(self):
        self.ui.addStationButton.clicked.connect(self.click_add_station)

    def click_add_station(self):
        self.dict["balance_id"] = self.ui.balanceCombo.currentText().split('|')[0]
        self.dict["thermometer_id"] = self.ui.thermometerCombo.currentText().split('|')[0]
        self.dict["barometer_id"] = self.ui.barometerCombo.currentText().split('|')[0]
        self.dict["hygrometer_id"] = self.ui.hygrometerCombo.currentText().split('|')[0]
        self.dict["name"] = self.ui.balanceCombo.currentText().split('|')[1]
        self.dict["building"] = self.ui.buildingEdit.text()
        self.dict["room"] = self.ui.roomEdit.text()

        self.db.add_station(self.dict)
        self.window.close()

    def __exit__(self):
        self.window.close()