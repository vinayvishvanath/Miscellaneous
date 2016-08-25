#!/usr/bin/python

""" SQLite helper module for persistant
    tracking of events and remediations.
"""

import os
import sqlite3


DB_FILE = 'db.sqlite'
SCHEMA = ('''
    CREATE TABLE events (
        id              INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        datestamp       DATE,
        device          TEXT,
        error_code      TEXT,
        error_message   TEXT,
        result          INTEGER)
''')


def _create_schema_if_not_exists(db_file=DB_FILE, schema=SCHEMA):
    """ Creates a SQLite database file if it does not already exist. """
    if not os.path.exists(db_file):
        with sqlite3.connect(db_file) as session:
            session.execute(schema)


def _open_session(db_file=DB_FILE):
    """ Opens a connection to the DB file.

        @return cursor      a database cursor
    """
    return sqlite3.connect(db_file)


def _insert_event(datestamp, device, error_code, error_message):
    """ Creates a new event based on the parameters provided.

        @return event_id    the unique database id of the event
    """
    session = _open_session()
    sql = ('''
        INSERT INTO events (datestamp, device, error_code, error_message)
        VALUES (?, ?, ?, ?)
    ''')
    cursor = session.cursor()
    cursor.execute(
        sql, (datestamp, device, error_code, error_message))
    event_id = cursor.lastrowid
    session.commit()
    session.close()
    return event_id


def insert_event(datestamp, timestamp, device, error_code, error_message):
    """ Creates a new event based on the parameters provided.

        @return event_id    the unique database id of the event
    """
    datestamp = '{0} {1}'.format(datestamp, timestamp)
    session = _open_session()
    sql = ('''
        SELECT id
        FROM events
        WHERE datestamp=? AND device=? AND error_code=? AND error_message=?
    ''')
    result = session.execute(
        sql, (datestamp, device, error_code, error_message)).fetchone()
    # Already exists, skip the insert to avoid duplication
    if result:
        event_id = result[0]
        return event_id
    return _insert_event(datestamp, device, error_code, error_message)


def get_event_by_id(event_id):
    """ Gets an event by its unique id.

        @return event       a dictionary of column names to this event's values
    """
    session = _open_session()
    sql = ('''
        SELECT datestamp, device, error_code, error_message, result
        FROM events
        WHERE id=?
    ''')
    event = session.execute(sql, (event_id,)).fetchone()
    session.close()
    return event


def get_events(limit=1000):
    """ Gets all events up to the limit specified. """
    session = _open_session()
    sql = ('''
        SELECT id, datestamp, device, error_code, error_message, result
        FROM events
        LIMIT ?
    ''')
    events = session.execute(sql, (limit,)).fetchall()
    session.close()
    return events


def update_event_result(event_id, result):
    """ Update an event's result.

        @return None
    """
    session = _open_session()
    sql = ('''
        UPDATE events
        SET result=?
        WHERE id=?
    ''')
    cursor = session.cursor()
    cursor.execute(sql, (event_id, result))
    session.commit()
    session.close()


_create_schema_if_not_exists()
