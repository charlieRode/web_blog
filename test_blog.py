# -*- coding: utf-8 -*-
from contextlib import closing
import pytest
from web_blog import app, connect_db, get_database_connection, init_db

TEST_DSN = 'dbname=test_blog user=store'


def clear_db():
    """To be run at the end of the testing session. Cleans the DB"""
    with closing(connect_db()) as db:
        db.cursor().execute("DROP TABLE entries")
        db.commit()


@pytest.fixture(scope='session')  # The scope is set to run this function once per invocation of py.test
def test_app():
    """configures the app for testing"""
    app.config['DATABASE'] = TEST_DSN
    app.config['TESTING'] = True


@pytest.fixture(scope='session')
def db(test_app, request):
    """initialize the entries table and drop it when finished"""
    init_db()

    def cleanup():
        clear_db()

    request.addfinalizer(cleanup)


@pytest.yield_fixture(scope='function')
def req_context(db):
    """run tests within a test request context so that 'g' is present"""
    with app.test_request_context('/'):
        yield
        conn = get_database_connection()
        conn.rollback()


def run_independent_query(query, params=[]):
    conn = get_database_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    return cur.fetchall()


def test_write_entry(req_context):
    from web_blog import write_entry
    expected = ("My Title", "My Text")
    write_entry(*expected)
    rows = run_independent_query("SELECT * FROM entries")
    assert len(rows) == 1
    for val in expected:
        assert val in rows[0]


def test_get_all_entries_empty(req_context):
    from web_blog import get_all_entries
    entries = get_all_entries()
    assert len(entries) == 0


def test_get_all_entries(req_context):
    from web_blog import get_all_entries, write_entry
    expected = ("My Title", "My Text")
    write_entry(*expected)
    entries = get_all_entries()
    assert len(entries) == 1
    for entry in entries:
        assert "My Title" == entry['title']
        assert "My Text" == entry['text']
        assert 'created' in entry


def test_empty_listing(db):
    actual = app.test_client().get('/').data
    expected = "No entires found"
    asser expected in actual

