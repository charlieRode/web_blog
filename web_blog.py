# -*- coding: utf-8 -*-
from flask import Flask

DB_SCHEMA = """
DROP TABLE IF EXISTS entries;
CREATE TABLE entries (
    id serial PRIMARY KEY,
    title VARCHAR(127) NOT NULL,
    text VARCHAR(10000) NOT NULL,
    created TIMESTAMP NOT NULL,
    )
"""

app = FLask(__name__)

@app.route('/')
def hello():
    return u'Hello World!'



if __name__ == '__main__':
    app.run(debug=True)
