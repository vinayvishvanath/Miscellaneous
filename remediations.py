#!/usr/bin/python
""" Remediations
"""

# Standard library modules
import re

# Local modules
import db
import ssh_helper


def linecard_failure(event_id, device_name, error_message):
    """ Linecard Failure Remediation """

    # Matches "5/1" from:
    #     Interface Ethernet5/1 is down (Interface removed)
    interface = re.match(r'.+(\d+)/\d+', error_message)
    if not interface:
        return

    module_number = interface.group(1)
    command = ('show module {module_number}'.format(
               module_number=module_number))

    # Open an SSH connection to the device
    ssh = ssh_helper.SSHSession(
        device=device_name,
        username='',
        passwd='')

    # Fetch output of "show module"
    show_module = ssh.write([command])

    status = show_module[3]
    if 'ok' in status.lower():
        command = ('show module uptime | '
                   'egrep -A 3 "Module {module_number}"'.format(
                   module_number=module_number))

        # Fetch output of "show module uptime"
        show_module_uptime = ssh.write([command])

        # If we wanted to dive deeper, we could alter the flow based on
        # how long its been online.  (It could be in a reboot loop...)
        uptime = show_module_uptime[3]
        print('[{0}]  NOTICE:  Module {1} is suspect but appears fine.\n'
              '[{0}]  {2}\n'.format(device_name, module_number, uptime))
    else:
        print('[{0}]  WARNING:  Module {0} may be faulty!\n'
              '[{0}]  {2}\n'.format(module_number, device_name, status))
    ssh.close()


def link_failure(event_id, device_name, error_message):
    """  Interface Link Down Remediation """

    # Matches "1/4" from:
    # Interface Ethernet1/4 is down (Link failure)
    interface = re.match(r'.+(\d+/\d+)', error_message)
    if not interface:
        return

    interface = interface.group(1)
    command = 'show interface eth {interface}'.format(interface=interface)

    # Open an SSH connection to the device
    ssh = ssh_helper.SSHSession(
        device=device_name,
        username='',
        passwd='')

    # Fetch output of "show interface"
    show_interface = ssh.write([command])

    for line in show_interface:
        interface_resets = re.match(r'^\s+(\d+) interface resets', line)
        if not interface_resets:
            continue

        reset_count = int(interface_resets.group(1))

        if reset_count <= 10:
            continue

        print('[{0}]  NOTICE:  Interface reset count [{1}] too '
              'high!  Checking for proper light levels.'.format(
              device_name, reset_count))

        # Check Rx Light Levels
        command = ('show interface eth {interface} transceiver '
                   'details | egrep "(Rx|rx)"'.format(
                   interface=interface))

        # Fetch output of "show interface transceiver details"
        show_int_transceiver = ssh.write([command])[1]

        # Matches "-3.84" from:
        #  Rx Power       -3.84 dBm
        rx_power = re.match(
            r'.+power\s+(-\d+.\d+) dbm',
            show_int_transceiver.lower())
        if not rx_power:
            continue

        # Check to see if it's less than our threshold
        rx_power = float(rx_power.group(1))
        if rx_power < -7.00:
            print('[{0}]  WARNING:  Rx Power for {interface} is '
                  'too low [{power} dBm]!  The fiber and '
                  'patch-panel ports should be checked.'.format(
                  device_name, interface=interface, power=rx_power))
    ssh.close()
