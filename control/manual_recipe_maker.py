__author__ = 'masslab'

import time
import re
import numpy as np
from decimal import Decimal
from config import good_responses


def emit_status(signal, status, arg):
    try:
        signal.emit(status % arg)
    except TypeError:
        signal.emit(status)


def manual_short_command(signal, conn, command, status_string, string_arg='', timeout=60):
    """ Send specified command (expects a balance response)to balance through "conn" and emit status signal """
    print "Command: " + command.strip('\r\n')
    emit_status(signal, status_string[0], string_arg)
    if not conn.isOpen():
        conn.open()
    # Wait until nothing can be read at the balance port
    while not timeout and conn.readlines():
        time.sleep(1)
        timeout -= 1
    # Write the command to the balance port and wait for response
    while timeout:
        time.sleep(1)
        conn.write(command)
        resp = conn.readlines()

        try:
            resp = float(resp[0])
        except ValueError:
            pattern = r'.?(\d*\.\d*)'
            match = re.findall(pattern, resp[0])
            resp = float(match[0])
        except IndexError:
            continue

        print resp
        print 'timeout: %s' % timeout
        if resp:
            return resp

        timeout -= 1
    conn.close()
    emit_status(signal, status_string[2], string_arg)
    return


def manual_id_command(signal, conn, command, status_string, timeout=60):
    """ Send id command to balance through "conn" and emit a special status signal """
    print "Command: " + command.strip('\r\n')
    signal.emit(status_string[0])
    if not conn.isOpen():
        conn.open()
    # Wait until nothing can be read at the balance port
    while not timeout and conn.readlines():
        time.sleep(1)
        timeout -= 1
    # Write the command to the balance port and wait for response
    while timeout:
        time.sleep(1)
        conn.write(command)
        resp = conn.readlines()
        if resp:
            conn.close()
            signal.emit(status_string[0] % ''.join(resp))
            return
        timeout -= 1
    conn.close()
    signal.emit('here')
    return


class ManualRecipeMaker:
    """ Generate a list of methods that will take the mass balance through a calibration

    Args:
        status_signal (pyqtSignal): pyqtSignal object declared in "ComparatorUi"
        conn (serial): Serial connection object
        main_dict (dictionary):  Relevant calibration metadata
        settings_dict (dictionary): Specific balance and run settings from balance settings ui
        instruction_dict (dictionary):  Balance commands and statuses from config file
    """
    def __init__(self, status_signal, conn, main_dict, settings_dict, instruction_dict):
        self.ss = status_signal
        self.c = conn
        self.m_d = main_dict
        self.s_d = settings_dict
        self.i_d = instruction_dict
        self.m = []
        self.a = []
        self.data_d = {}
        self.runs = 5  # Number of runs you want to do??????
        self.make_recipe()

    def make_recipe(self):
        pass
