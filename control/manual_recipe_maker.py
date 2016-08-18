__author__ = 'masslab'

import time
import re


def emit_status(signal, status, arg):
    try:
        signal.emit(status % arg)
    except TypeError:
        signal.emit(status)


def manual_short_command(signal, conn, command, status_string, string_arg='', timeout=60):
    """ Send specified command (expects a balance response)to balance through "conn" and emit status signal """
    print "Command: " + command.strip('\r\n')
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
            pattern = r'(.?\d+\.\d+)'
            match = re.findall(pattern, resp[0])
            resp = float(match[0])
        except IndexError:
            continue

        print 'reading:', resp
        print 'timeout:', timeout
        if resp:
            return resp
        elif resp == 0.0 or float(resp) == 0.0:
            return resp

        timeout -= 1

    conn.close()
    signal.emit('Error reading the balance.')
    return None


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
    signal.emit('Error connecting. Check the port again')
    return


def manual_short_command_no_resp(signal, conn, command, status_string, string_arg='', timeout=5):
    """ Send specified command (expects no response) to balance through "conn" and emit status signal """
    print "Command: " + command.strip('\r\n')
    emit_status(signal, status_string[0], string_arg)
    if not conn.isOpen():
        conn.open()
    # Wait until nothing can be read at the balance port
    while not timeout and conn.readlines():
        time.sleep(1)
        timeout -= 1
    # Write the command to the balance port and wait for response
    conn.write(command)
    time.sleep(3)
    conn.close()
    emit_status(signal, status_string[1], string_arg)
    return
