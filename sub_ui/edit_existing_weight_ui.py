__author__ = 'masslab'


from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtCore import QObject
import re

try:
    _encoding = QtGui.QApplication.UnicodeUTF8

    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class EditExistingWeightUI(QObject):
    """
    Provides functionality to the UI that allows the user to add a weight to the database.
    This UI opens when the user clicks the button "Edit Weights" in the DB Access tab of the Main UI
    """

    def __init__(self, cls):
        """

        :param db: This is an instance of MainUI.db, allowing this class to access databaseORM
        """
        self.db = cls.db

        super(QObject, self).__init__()
        self.window = QtGui.QDialog(None, QtCore.Qt.WindowSystemMenuHint |
                                    QtCore.Qt.WindowTitleHint |
                                    QtCore.Qt.WindowMinMaxButtonsHint)
        self.window.setSizeGripEnabled(True)

        # Load the UI into self.ui
        self.ui = uic.loadUi('sub_ui/Edit_Weight.ui', self.window)

        # Populate the weight tree
        self.populate_tree()

        # Initialize weight name
        self._name = None

        # Disable the editing fields
        self.enable_edits(0)

        # Set up the event handlers
        self.callback_connector()

        # Execute the ui
        self.window.exec_()

    def callback_connector(self):
        self.ui.weightTree.itemDoubleClicked.connect(self.item_clicked)
        self.ui.submitButton.clicked.connect(self.click_submit)
        self.ui.cancelButton.clicked.connect(self.__exit__)

    def populate_tree(self):

        # Get customer names
        customers = self.db.get_customer_names()

        count = 0
        for customer_name in customers:
            item = QtGui.QTreeWidgetItem()
            item.setText(0, customer_name)
            item.setFlags(QtCore.Qt.ItemIsEnabled)

            self.ui.weightTree.addTopLevelItem(item)

            # Get customer weight names
            customer_weights = self.db.get_customer_weight_names(customer_name)

            count_2 = 0
            for weight in customer_weights:
                item_2 = QtGui.QTreeWidgetItem(item)
                self.ui.weightTree.topLevelItem(count).child(count_2).setText(0, "EXT|" + weight)
                count_2 += 1

            count += 1

    def item_clicked(self, item):
        # Enable the edits
        self.enable_edits(1)

        if item.childCount() == 0:
            regex = r'\|  (.*)'
            self._name = re.findall(regex, item.text(0))[0]
            weight_info = [r for r in self.db.get_external_weight_info(self._name)][0]

            # Populate the properties line edits
            self.ui.nameEdit.setText(self._name)
            self.ui.nominalEdit.setText(str(weight_info[1]))
            self.ui.unitEdit.setText(weight_info[0])
            self.ui.customerEdit.setText(weight_info[2])
            self.ui.densityEdit.setText(str(weight_info[3]))
            self.ui.volExpEdit.setText(str(weight_info[4]))
            self.ui.densityUncEdit.setText(str(weight_info[5]))
        else:
            pass

    def click_submit(self):
        self.db.update_external_weight_info(self._name,
                                            self.ui.nominalEdit.text(),
                                            self.ui.unitEdit.text(),
                                            self.ui.customerEdit.text(),
                                            self.ui.densityEdit.text(),
                                            self.ui.densityUncEdit.text(),
                                            self.ui.volExpEdit.text())
        self.update_event()

    def update_event(self):
        QtGui.QMessageBox.information(self.ui.weightTree, 'Success!', 'Successfully updated!')

        self.ui.weightTree.clear()
        self.populate_tree()
        self.clear_edits()

    def enable_edits(self, bool):
        self.ui.nameEdit.setEnabled(bool)
        self.ui.unitEdit.setEnabled(bool)
        self.ui.nominalEdit.setEnabled(bool)
        self.ui.customerEdit.setEnabled(bool)
        self.ui.densityUncEdit.setEnabled(bool)
        self.ui.densityEdit.setEnabled(bool)
        self.ui.volExpEdit.setEnabled(bool)

    def clear_edits(self):
        self.ui.nameEdit.clear()
        self.ui.unitEdit.clear()
        self.ui.nominalEdit.clear()
        self.ui.customerEdit.clear()
        self.ui.densityUncEdit.clear()
        self.ui.densityEdit.clear()
        self.ui.volExpEdit.clear()

    def __exit__(self):
        self.window.close()