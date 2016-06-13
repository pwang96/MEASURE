__author__ = 'masslab'

from PyQt4 import QtGui, QtCore

try:
    _encoding = QtGui.QApplication.UnicodeUTF8

    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


def populate_enviro_tree(main, cls):
    """

    :param main: instance of MainUI class
    :param cls: instance of EditMetersUI class
    :return:
    """

    cls.ui.enviroTree.setHeaderLabel('')
    # Populate the tree
    cls.ui.enviroTree.addTopLevelItem(general_tree(cls, "Thermometers", main.db.get_thermometers()))
    cls.ui.enviroTree.addTopLevelItem(general_tree(cls, "Barometers", main.db.get_barometers()))
    cls.ui.enviroTree.addTopLevelItem(general_tree(cls, "Hygrometers", main.db.get_hygrometers()))


def general_tree(cls, top_title, db_query):
    top = QtGui.QTreeWidgetItem(cls.ui.enviroTree)
    top.setText(0, top_title)
    for t in db_query:
        child = QtGui.QTreeWidgetItem()
        child.setText(0, str(t))
        top.addChild(child)

    return
