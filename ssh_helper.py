""" SSH Connection Handler for Network Devices

    This module supports SSH-based communication natively from
    Python using the Paramiko module.  Interactive prompts and IPv6
    are both supported here.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import socket
import time

# Third-party
import paramiko


class SSHSession(object):
    """ Opens an SSH session to the device and returns a connection object. """

    def __init__(self, device, username, passwd, debug=False):
        self.device = device
        self.username = username
        self.passwd = passwd
        self.debug = debug
        self._connect()

    def _connect(self):
        """ Performs the initial SSH connection setup.  This is an internal
            method called when an instance of this class is created.
        """
        self.ssh_conn = paramiko.SSHClient()
        if self.debug:
            self.ssh_conn.log = paramiko.common.logging.basicConfig(
                level=paramiko.common.DEBUG)
        # "known_hosts" is ignored, so there's no potential for mismatched keys
        self.ssh_conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # The default for allow_agent (False) breaks SSH to some devices
        self.ssh_conn.connect(self.device, username=self.username,
                              password=self.passwd, allow_agent=False)
        self.ssh_shell = self.ssh_conn.invoke_shell()
        self.ssh_shell.set_combine_stderr(True)
        self.ssh_shell.setblocking(True)

    def write(self, commands, delay=2, read_until='#', timeout=30,
              wait_for_output=True):
        """ Writes the commands provided and attempts to read the output
            until the "read_until" value is found, or until the timeout
            (seconds) is reached.  The delay parameter is a sleep time
            between commands.
        """
        self.ssh_shell.settimeout(timeout)

        for command in commands:
            self.ssh_shell.send('{0}\n'.format(command))
            time.sleep(delay)

        self.output_buffer = ''
        if wait_for_output:
            while not re.search(read_until, self.output_buffer):
                if self.ssh_shell.recv_ready():
                    try:
                        resp = self.ssh_shell.recv(8096)
                    except socket.timeout:
                        error = ('Timeout exceeded while attempting to read '
                                 'response after issuing "{0}" to {1}.'.format(
                                 command, self.device))
                        raise Exception(error)
                    self.output_buffer += resp
                else:
                    time.sleep(1)
        return self.output_buffer

    def close(self):
        self.ssh_conn.close()


import socket
if socket.gethostname() in ['DEVBOX01']:
    from mock_outputs import SSHSession
