# -*- coding: utf-8 -*-
from flask import Flask
from flask import g
import os
import psycopg2
from contextlib import closing

DB_SCHEMA = """
DROP TABLE IF EXISTS entries;
CREATE TABLE entries (
    id serial PRIMARY KEY,
    title VARCHAR(127) NOT NULL,
    text VARCHAR(10000) NOT NULL,
    created TIMESTAMP NOT NULL
    )
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


@app.teardown_request #This function will be called after the request/response cycle is completed (even if an exception is raised)
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


@app.route('/')
def hello():
    return u'Hello World!'



if __name__ == '__main__':
    app.run(debug=True)
