#! /usr/bin/env python
import pyramid
import pytest
import os
from pyramid import testing
import psycopg2
from contextlib import closing
from webapp import DB_LOCALS_SCHEMA, DB_TWEETS_SCHEMA

TEST_DSN = 'dbname=test_wazzap user=efrain-petercamacho'


WRITE_LOCALS_ENTRY = """
INSERT INTO "locals" ("venue", "screen_name", "address") VALUES(%s, %s, %s)
"""

########################
# TESTING - SETUP
########################


@pytest.fixture(scope='session')
def db(request):
    """set up and tear down a database"""
    settings = {'db': TEST_DSN}
    init_db(settings)

    def cleanup():
        clear_db(settings)

    request.addfinalizer(cleanup)

    return settings


@pytest.fixture(scope='function')
def app(db):
    from webapp import main
    from webtest import TestApp
    os.environ['DATABASE_URL'] = TEST_DSN
    app = main()
    return TestApp(app)


def init_db(settings):
    with closing(connect_db(settings)) as db:
        db.cursor().execute(DB_LOCALS_SCHEMA)
        db.cursor().execute(DB_TWEETS_SCHEMA)
        db.commit()


def clear_db(settings):
    with closing(connect_db(settings)) as db:
        db.cursor().execute("DROP TABLE locals CASCADE")
        db.commit()


def connect_db(settings):
    """Return a connection to the configured database"""
    return psycopg2.connect(settings['db'])


def write_local(local_info_tuple, connection):
    cursor = connection.cursor()
    cursor.execute(WRITE_LOCALS_ENTRY, local_info_tuple)
    connection.commit()


########################
# TESTING
########################


def test_listing(app):
    """Test that application website is functional on
    virtual machine"""
    response = app.get('/')
    assert response.status_code == 200


    test = connect_db(settings)
    print test

def test_write_local(settings):
    """Test the write command with a generic string"""

    write_local(('Central Cinema', 'CentralCinema',
                '1411 21st Avenue, Seattle, WA 98122'), db)
    cursor = db.cursor()
    query = cursor.execute("SELECT * FROM locals")
    print query
    assert True




