__author__ = 'masslab'


def populate_enviro_menu(cls):
    """
    Adds temp, pressure, and humidity to the dropdown menu in the PLOT tab

    """
    cls.ui.chooseEnviroCombo.addItems(["Temperature", "Pressure", "Humidity"])  # PLOT TAB: Populates combo box

