# -*- coding: utf-8 -*-
from flask import Flask
from flask import g
from flask import render_template
from flask import abort, request, url_for, redirect
import os
import psycopg2
from contextlib import closing
import datetime

DB_SCHEMA = """
DROP TABLE IF EXISTS entries;
CREATE TABLE entries (
    id serial PRIMARY KEY,
    title VARCHAR(127) NOT NULL,
    text VARCHAR(10000) NOT NULL,
    created TIMESTAMP NOT NULL
    )
"""

DB_ENTRY_RETRIEVAL = """
SELECT id, title, text, created FROM entries ORDER BY created DESC
"""

DB_ENTRY_INSERT = """
INSERT INTO entries (title, text, created) VALUES (%s, %s, %s)
"""

DB_ENTRY_DELETE = """
DELETE FROM entries WHERE id=(%s)
"""

DB_ENTRY_UPDATE = """
UPDATE entries SET title=(%s), text=(%s) WHERE id=(%s)
"""

app = Flask(__name__)

app.config['DATABASE'] = os.environ.get(
    'DATABASE_URL', 'dbname=web_blog user=store'
)


def connect_db():
    """Return a connection to the database"""
    return psycopg2.connect(app.config['DATABASE'])


def init_db():
    """Initialize the database
    WARNING: executing this function will drop existing tables.
    """
    with closing(connect_db()) as db:
        db.cursor().execute(DB_SCHEMA)
        db.commit()


def get_database_connection():
    db = getattr(g, 'db', None)
    if db is None:
        g.db = connect_db()
        db = g.db
    return db


@app.teardown_request  # This function will be called after the request/response cycle is completed (even if an exception is raised)
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        if exception and isinstance(exception, psycopg2.Error):
            # if an exception of type psycopg2.Error is raised,
            # rollback any existing transaction
            db.rollback()
        else:
            db.commit()
        db.close()


def write_entry(title, text):
    """writes a title, text and created timestamp to database table entries"""
    if not (title and text):
        raise ValueError("A title and text body are both required")
    conn = get_database_connection()
    cur = conn.cursor()
    now = datetime.datetime.utcnow()
    cur.execute(DB_ENTRY_INSERT, [title, text, now])


def delete_entry(entry_id):
    """delete an entry from the table"""
    conn = get_database_connection()
    cur = conn.cursor()
    cur.execute(DB_ENTRY_DELETE, [entry_id])


def update_entry(title, text, entry_id):
    """update title and text for an entry"""
    conn = get_database_connection()
    cur = conn.cursor()
    cur.execute(DB_ENTRY_UPDATE, [title, text, entry_id])


def get_all_entries():
    """returns a list of entries as dicts"""
    conn = get_database_connection()
    cur = conn.cursor()
    cur.execute(DB_ENTRY_RETRIEVAL)
    entries = cur.fetchall()
    keys = ('id', 'title', 'text', 'created')
    entries_as_dicts = []
    for entry in entries:
        entries_as_dicts.append(dict(zip(keys, entry)))
    return entries_as_dicts


@app.route('/')
def show_entries():
    entries = get_all_entries()  # list of dicts
    return render_template('list_entries.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    try:
        title = request.form['title']
        text = request.form['text']
        write_entry(title, text)
    except psycopg2.Error:
        abort(500)  # Internal Server Error
    return redirect(url_for('show_entries'))

"""
#@app.route('/edit', methods=['POST'])
#def edit_entry():
#    try:
#        entry_id = request.form['id']
"""

@app.route('/delete', methods=['POST'])
def remove_entry():
    try:
        entry_id = request.form['id']
        delete_entry(entry_id)
    except psycopg2.Error:
        abort(500)
    return redirect(url_for('show_entries'))


if __name__ == '__main__':
    app.run(debug=True)
