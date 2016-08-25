
import time


SHOW_MODULE_5 = ('''switch1# show module 5
Mod  Ports  Module-Type                         Model              Status
---  -----  ----------------------------------- ------------------ ----------
5    48     1/10 Gbps Ethernet Module           F8-A1234-48        ok

Mod  Sw              Hw
---  --------------  ------
5    10.10(3)        1.0


Mod  MAC-Address(es)                         Serial-Num
---  --------------------------------------  ----------
5    00-00-00-2d-bc-a0 to 00-00-00-2d-bc-d3  ABCD123EFG

Mod  Online Diag Status
---  ------------------
5    Pass

Chassis Ejector Support: Enabled
Ejector Status:
Left ejector CLOSE, Right ejector CLOSE, Module HW does support ejector based shutdown.''')


SHOW_MODULE_5_UPTIME = ('''switch1# show module uptime | egrep -A 3 "Module 5"
------ Module 5 -----
Module Start Time:    Thu Apr  2 14:40:07 2015
Up Time:             45 days, 19 hours, 35 minutes, 45 seconds''')


SHOW_INTERFACE = ('''switch2# show interface ethernet 1/4 | egrep "(is up|is down|flapped|rate|input errors|input discard|output errors|interface resets)"
Ethernet1/4 is up
  Last link flapped 1d03h
  30 seconds input rate 730310680 bits/sec, 91288835 bytes/sec, 72677 packets/sec
  30 seconds output rate 505273896 bits/sec, 63159237 bytes/sec, 58752 packets/sec
    input rate 553.84 Mbps, 57.78 Kpps; output rate 495.41 Mbps, 56.99 Kpps
    0 input with dribble  117824 input discard(includes ACL drops)
    0 output errors  0 collision  0 deferred  0 late collision
  229 interface resets''')


SHOW_INTERFACE_TRANSCEIVER = ('''switch2# show int eth 1/45 transceiver details | egrep "(Rx|rx)"
  Rx Power       -8.84 dBm       1.99 dBm  -13.97 dBm   -1.00 dBm     -9.91 dBm''')


class SSHSession(object):
    """ A mock object to act like an SSH connection, but instead returns
        pre-staged outputs based on parsing of commands provided.
    """

    def __init__(self, device, username='', passwd='', debug=False):
        self.device = device
        self.username = username
        self.passwd = passwd

    def write(self, commands):
        output = ''
        for command in commands:
            if command.startswith('show module 5'):
                output += SHOW_MODULE_5
            elif command.startswith('show module uptime'):
                output += SHOW_MODULE_5_UPTIME
            elif command.startswith('show interface') and (
                    'transceiver' in command):
                output += SHOW_INTERFACE_TRANSCEIVER
            elif command.startswith('show interface'):
                output += SHOW_INTERFACE
        time.sleep(2)
        return output.rsplit('\n')

    def close(self):
        return
