#!/usr/bin/python
""" An example of parsing Syslog messages
    and performing remediations.
"""

# Standard library modules
import re
import sys

# Local modules
import db
import remediations


SYSLOG_FILE = 'syslog.txt'

# Regular expressions by section, overall this matches:
#     2015 Apr  2 14:25:06 switch1 %ETHPORT-5-IF_DOWN_INTERFACE_REMOVED: 
#     Interface Ethernet5/1 is down (Interface removed)
DATESTAMP_RE = r'(\d+\s+\w+\s+\d+)'  
TIMESTAMP_RE = r'(\d+:\d+:\d+)'     
DEVICE_NAME_RE = r'(\S+)'          
                                    
                                   
ERROR_CODE_RE = r'%(\S+):'           
ERROR_MSG_RE = r'(.*)'               
COLUMN_DELIMITER_RE = r'\s+'        


SYSLOG_RE = (
    DATESTAMP_RE + COLUMN_DELIMITER_RE +
    TIMESTAMP_RE + COLUMN_DELIMITER_RE +
    DEVICE_NAME_RE + COLUMN_DELIMITER_RE +
    ERROR_CODE_RE + COLUMN_DELIMITER_RE +
    ERROR_MSG_RE)

# Event result codes for database tracking
EVENT_RESULTS = {
    'REMEDIATION_FAILED': 1,
    'REMEDIATION_COMPLETED': 2}


ERROR_CODES_TO_REMEDIATIONS = {
    'IF_DOWN_INTERFACE_REMOVED':  remediations.linecard_failure,
    'IF_DOWN_LINK_FAILURE':  remediations.link_failure,
}


def read_logs(log_file=SYSLOG_FILE):
    """ Reads the syslog file """
    with open(log_file, mode='r') as syslog:
        log_lines = syslog.readlines()
    return log_lines


def parse_logs_to_events(log_lines, regex=SYSLOG_RE):
    """ Parses log lines """
    event_ids = []
    for line in log_lines:
        matched = re.match(regex, line)
        if not matched:
            continue

        datestamp, timestamp, device_name, error_code, error_message = (
            matched.groups())

        # Create an event in our DB
        event_id = db.insert_event(
            datestamp, timestamp, device_name, error_code, error_message)
        event_ids.append(event_id)

    return event_ids


def run_remediation(event_id):
    """ Runs remediation logic for known error codes """

    datestamp, device_name, error_code, error_message, result = (
        db.get_event_by_id(event_id))

    for known_error_code in ERROR_CODES_TO_REMEDIATIONS:

        if known_error_code in error_code:

            print('[{0}]  NOTICE:  Found a known error [{1}] - attempting '
                  'remediation.'.format(device_name, error_code))

            # Fetch the function assigned to this error code
            remediation = ERROR_CODES_TO_REMEDIATIONS[known_error_code]

            # Run that function, passing in the event_id.
            remediation(event_id, device_name, error_message)


def main():
    """ Main program logic """

    log_lines = read_logs()

    event_ids = parse_logs_to_events(log_lines)
    print('Parsed {0} events from syslog'.format(len(event_ids)))

    for event_id in event_ids:
        print('Running remediation for event_id:  {0}'.format(event_id))
        run_remediation(event_id)


if __name__ == '__main__':
    sys.exit(main())
