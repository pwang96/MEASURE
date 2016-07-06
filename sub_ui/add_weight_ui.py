__author__ = 'masslab'


from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtCore import QObject
from populate_ui.populate_tree_widget import populate_tree_widget


class AddWeightUI(QObject):
    """
    Provides functionality to the UI that allows the user to add a weight to the database.
    This UI opens when the user clicks the button "Edit Weights" in the DB Access tab of the Main UI
    """

    def __init__(self, cls):
        """

        :param cls: This is an instance of MainUI, allowing this class to access databaseORM
        """
        self.db = cls.db
        self.cls = cls

        super(QObject, self).__init__()
        self.window = QtGui.QDialog(None, QtCore.Qt.WindowSystemMenuHint |
                                    QtCore.Qt.WindowTitleHint |
                                    QtCore.Qt.WindowMinMaxButtonsHint)
        self.window.setSizeGripEnabled(True)

        # Load the UI into self.ui
        self.ui = uic.loadUi('sub_ui/Add_Weight.ui', self.window)

        # Set up the event handlers
        self.callback_connector()

        # Initialize the dictionary that holds the weight's attributes
        self.dict = {"weightName":None,
                     "nominal":None,
                     "units":None,
                     "custName":None,
                     "density":None,
                     "uncert":None,
                     "vol":None,
                     "comments":None}

        # Execute the ui
        self.window.exec_()

    def callback_connector(self):
        self.ui.addWeightButton.clicked.connect(self.click_add_weight)

    def click_add_weight(self):
        self.dict["weightName"] = self.ui.weightNameEdit.text()
        self.dict["nominal"] = self.ui.weightEdit.text()
        self.dict["units"] = self.ui.unitEdit.text()
        self.dict["custName"] = self.ui.custNameEdit.text()
        self.dict["density"] = self.ui.densityEdit.text()
        self.dict["uncert"] = self.ui.uncertEdit.text()
        self.dict["vol"] = self.ui.volEdit.text()
        self.dict["comments"] = self.ui.commentsEdit.text()

        self.db.add_weight(self.dict)  # add the weight to the database

        # Update the weight tree in the calibrations tab
        self.cls.ui.weightTree.clear()
        populate_tree_widget(self.cls)

        self.window.close()

    def __exit__(self):
        self.window.close()