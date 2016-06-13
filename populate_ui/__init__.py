__author__ = 'masslab'

from object_settings import object_settings
from populate_tree_widget import populate_tree_widget
from populate_balance_menu import populate_balance_menu
from populate_design_menu import populate_design_menu
from populate_table_widget import populate_table_widget
from populate_enviro_menu import populate_enviro_menu


class PopulateUI:

    def __init__(self, main):
        # Populating widgets in the tabs
        object_settings(main)  # CALIBRATION TAB
        populate_tree_widget(main)
        populate_balance_menu(main)

        populate_enviro_menu(main)  # PLOT TAB

    def design_menu(self, main):
        populate_design_menu(main)

    def table_widget(self, main):
        populate_table_widget(main)
