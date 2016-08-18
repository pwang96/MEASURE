__author__ = 'masslab'


def populate_design_menu(cls):
    """
    Gets all the designs that are compatible with the selected balance.
    All balances have a certain number of positions (99 for manual balances), and
    a "type". Only designs that require the same or fewer number of positions and match
    the balance "type" are added to the design menu.

    :param cls: Instace of MainUI
    :return: None
    """
    design_names = cls.db.get_viable_designs(cls.main_dict['balance id'])
    cls.ui.designCombo.clear()
    cls.ui.designCombo.addItems(design_names)
