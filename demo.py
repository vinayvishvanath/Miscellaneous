#!/usr/local/bin/python3

# Copyright 2015-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE-examples file in the root directory of this source tree.

""" An example of parsing Syslog messages
    and performing remediations.

    This example was created for NetOps Coding 101, a coding tutorial
    presented at NANOG.  Join the community at
    https://www.facebook.com/groups/netengcode/ for follow-up discussion &
    collaboration with your peers!
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# Standard library modules
import re
import time

# Local modules
import ssh_helper


# Regular expressions by section, overall this matches:
#     2015 Apr  2 14:25:06 switch1 %ETHPORT-5-IF_DOWN_INTERFACE_REMOVED:
#     Interface Ethernet5/1 is down (Interface removed)
DATESTAMP_RE = r'(\d+\s+\w+\s+\d+)'  # Group 1:  year month day
TIMESTAMP_RE = r'(\d+:\d+:\d+)'      # Group 2:  hours:mins:secs
DEVICE_NAME_RE = r'(\S+)'            # Group 3:  device name
                                     #           (capital S matches all
                                     #            non-space characters)
ERROR_CODE_RE = r'%(\S+):'           # Group 4:  error code
ERROR_MSG_RE = r'(.*)'               # Group 5:  everything else (greedy match)
COLUMN_DELIMITER_RE = r'\s+'         # space(s)

# Combine all of the regexes together
SYSLOG_RE = (
    DATESTAMP_RE + COLUMN_DELIMITER_RE +
    TIMESTAMP_RE + COLUMN_DELIMITER_RE +
    DEVICE_NAME_RE + COLUMN_DELIMITER_RE +
    ERROR_CODE_RE + COLUMN_DELIMITER_RE +
    ERROR_MSG_RE)


# Read the syslog file
SYSLOG_FILE = 'syslog.txt'
with open(SYSLOG_FILE, mode='r') as syslog:
    log_lines = syslog.readlines()

# Parsing time!
for line in log_lines:
    matched = re.match(SYSLOG_RE, line)
    if not matched:
        continue
    print('.' * 80)

    # Expand the result of "matched.groups()" to individual variables
    datestamp, timestamp, device_name, error_code, error_message = (
        matched.groups())

    print('NEW LOG EVENT:\n'
          '    {date}:{time}  {device}  {error_code}\n'
          '        {error_message}\n'.format(
          date=datestamp, time=timestamp, device=device_name,
          error_code=error_code, error_message=error_message))


    ### --- Begin of Module Failure Remediation --- ###
    if 'IF_DOWN_INTERFACE_REMOVED' in error_code:

        print('[{0}]  Log event matched remediation for:  {1}'.format(
              device_name, error_code))

        # Matches "5/1" from:
        #     Interface Ethernet5/1 is down (Interface removed)
        interface = re.match(r'.+(\d+)/\d+', error_message)
        if not interface:
            continue

        module_number = interface.group(1)
        command = ('show module {module_number}'.format(
                   module_number=module_number))

        # Open an SSH connection to the device
        ssh = ssh_helper.SSHSession(
            device=device_name,
            username='',
            passwd='')

        print('[{0}]  Checking status of module {1}.'.format(
              device_name, module_number))

        # Fetch output of "show module"
        show_module = ssh.write([command])

        status = show_module[3]
        if 'ok' in status.lower():
            print('[{0}]  Module is currently online.  Checking uptime.'.format(
                  device_name))
            command = ('show module uptime | '
                       'egrep -A 3 "Module {module_number}"'.format(
                       module_number=module_number))

            # Fetch output of "show module uptime"
            show_module_uptime = ssh.write([command])

            # If we wanted to dive deeper, we could alter the flow based on
            # how long its been online.  (It could be in a reboot loop...)
            uptime = show_module_uptime[3]
            print('[{0}]  Module uptime appears sane - taking no further '
                  'action.\n'.format(device_name, module_number))
        else:
            print('[{0}]  Module {1} may be faulty!  Current status:  '
                  '{2}'.format(device_name, module_number, status))
        ssh.close()
        ### --- End of Module Failure Remediation --- ###

    ### --- Begin of Interface Link Down Remediation --- ###
    elif 'IF_DOWN_LINK_FAILURE' in error_code:

        print('[{0}]  Log event matched remediation for:  {1}'.format(
              device_name, error_code))

        # Matches "1/4" from:
        # Interface Ethernet1/4 is down (Link failure)
        interface = re.match(r'.+(\d+/\d+)', error_message)
        if not interface:
            continue

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
                print('[{0}]  Interface reset count of {count} for {interface} '
                      'appears sane.  Taking no further action.'.format(
                      device_name, count=reset_count, interface=interface))
                continue

            print('[{0}]  Flapping link detected for interface '
                  'Ethernet{interface}!  Interface reset count of '
                  '{count} exceeds threshold!'.format(
                  device_name, reset_count, interface=interface,
                  count=reset_count))

            # Check Rx Light Levels
            print('[{0}]  Checking light levels for interface '
                  'Ethernet{interface}'.format(
                  device_name, interface=interface))
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
                print('[{0}]  Unable to parse Rx power for interface '
                      '{interface}'.format(device_name, interface=interface))
                continue

            # Check to see if it's less than our threshold
            rx_power = float(rx_power.group(1))
            if rx_power < -7.00:
                print('[{0}]  Rx Power for interface Ethernet{interface} is '
                      'too low [{power} dBm]!'.format(
                      device_name, interface=interface, power=rx_power))
                print('[{0}]  This link should be drained it\'s fiber and '
                      'patch-panel ports may need cleaned or replaced.'.format(
                      device_name))
            else:
                print('[{0}]  Rx power for interface Ethernet{interface} '
                      'appears sane.  Taking no further action.'.format(
                      device_name, interface=interface))
        ssh.close()
        ### --- End of Interface Link Down Remediation --- ###
    time.sleep(1)
print('.' * 80)
print()
