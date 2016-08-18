__author__ = 'masslab'

from utility.air_density_solver import air_density_solver
from PyQt4 import QtGui, QtCore, uic
from error_message import ErrorMessage


class AirDensityCalc(QtGui.QWidget):
    """
    Provides functionality to the UI that allows the user to add a weight to the database.
    This UI opens when the user clicks the button "Edit Weights" in the DB Access tab of the Main UI
    """

    def __init__(self):
        """

        """

        super(QtGui.QWidget, self).__init__()
        self.window = QtGui.QDialog(None, QtCore.Qt.WindowSystemMenuHint |
                                    QtCore.Qt.WindowTitleHint |
                                    QtCore.Qt.WindowMinMaxButtonsHint)
        self.window.setSizeGripEnabled(True)

        # Load the UI into self.ui
        self.ui = uic.loadUi('sub_ui/AirDensityCalculator.ui', self.window)

        # Populate the combo boxes
        self.ui.tempCombo.addItems(['Celsius', 'Fahrenheit'])
        self.ui.pressCombo.addItems(['Pa', 'mmHg', 'atm'])

        # Set up the event handlers
        self.ui.calculateButton.clicked.connect(self.calculate)
        self.ui.clearButton.clicked.connect(self.clear)

        self.ui.resultBrowser.setFontPointSize(20)

        # Execute the ui
        self.window.exec_()

    def calculate(self):
        # Get the temperature in Celsius
        if self.ui.tempCombo.currentText() == 'Celsius':
            temp = float(self.ui.tempEdit.text())
        else:
            temp = (float(self.ui.tempEdit.text()) - 32) * float(5)/9

        # Get the temperature in Pascals
        if self.ui.pressCombo.currentText() == 'Pa':
            press = float(self.ui.pressEdit.text())
        elif self.ui.pressCombo.currentText() == 'mmHg':
            # 1 mmHg = 133.322365 Pa
            press = float(self.ui.pressEdit.text()) * 133.322365
        else:
            # 1 atm = 101325 Pa
            press = float(self.ui.pressEdit.text()) * 101325

        humid = float(self.ui.humidEdit.text())
        if humid > 1:
            ErrorMessage('Humidity should be less than 1.\nResulting air pressure is incorrect')

        air_density = air_density_solver(temp, press, humid)

        self.ui.resultBrowser.append('Air density: ' + str(air_density))

    def clear(self):
        # clear all the text edits and the browser
        self.ui.tempEdit.clear()
        self.ui.pressEdit.clear()
        self.ui.humidEdit.clear()
        self.ui.resultBrowser.clear()

    def __exit__(self):
        self.window.close()

if __name__ == '__main__':
    AirDensityCalc()