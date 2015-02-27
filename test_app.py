#! /usr/bin/env python
import pyramid
import pytest
import httplib
import urllib
import os
from pyramid import testing
import psycopg2
from contextlib import closing
from webapp import DB_LOCALS_SCHEMA, DB_TWEETS_SCHEMA
from webapp import pull_tweets, WRITE_TWEET
from tweepy_inter import authorize
from tweepy_inter import fetch_user_statuses


TEST_DSN = 'dbname=test_wazzap user=efrain-petercamacho'
dbname = "dbname=test_wazzap user=efrain-petercamacho"

WRITE_LOCALS_ENTRY = """
INSERT INTO "locals" ("venue", "screen_name", "address") VALUES(%s, %s, %s)
"""

########################
# TESTING - SETUP
########################


@pytest.fixture(scope='session')
def db(request):
    """set up and tear down a database"""
    init_db()

    def cleanup():
        clear_db()

    request.addfinalizer(cleanup)


@pytest.fixture(scope='function')
def app(db):
    from webapp import main
    from webtest import TestApp
    os.environ['DATABASE_URL'] = TEST_DSN
    app = main()
    return TestApp(app)


def init_db():
    with closing(connect_db()) as conn:
        cursor = conn.cursor()
        cursor.execute(DB_LOCALS_SCHEMA)
        cursor.execute(DB_TWEETS_SCHEMA)
        conn.commit()


def clear_db():
    with closing(connect_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE locals CASCADE")
        conn.commit()


def connect_db():
    """Return a connection to the configured database"""
    return psycopg2.connect(dbname)


def write_local(local_info_tuple):
    with closing(connect_db()) as conn:
        cursor = conn.cursor()
        cursor.execute(WRITE_LOCALS_ENTRY, local_info_tuple)
        conn.commit()


def read_db():
    with closing(connect_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM locals")
        results = cursor.fetchall()
        conn.commit()
    return results


def pull_tweets(target_twitter_handle):
    with closing(connect_db()) as conn:
        cursor = conn.cursor()
        results = fetch_user_statuses(
            authorize(), target_twitter_handle)
        print results
        cursor.executemany(WRITE_TWEET, results)
        conn.commit()


def read_db_tweets():
    with closing(connect_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tweets")
        results = cursor.fetchall()
        conn.commit()
    return results

########################
# TESTING
########################


def test_listing(app):
    """Test that application website is functional on
    virtual machine"""
    response = app.get('/')
    assert response.status_code == 200


def test_webpage():
    """Test that the webpage is up and running"""
    assert True


def test_write_local():
    """Test the write command with a generic string"""
    location = ('Central Cinema', 'CentralCinema',
                '1411 21st Avenue, Seattle, WA 98122')
    expected_output = [(1, 'Central Cinema', 'CentralCinema',
                '1411 21st Avenue, Seattle, WA 98122')]
    write_local(location)
    query = read_db()
    print "This is the query: {} ".format(query)
    assert query == expected_output


def test_website_connetion():
   """Tests to see if we are on the homepage"""
   conn = httplib.HTTPConnection('ec2-52-10-224-242.us-west-2.compute.amazonaws.com')
   conn.request("HEAD", '')
   assert conn.getresponse().status == 200


def test_write_tweet():
    """Test that pulled tweets are written to the database"""
    # pull_tweets('HenryMGrantham')
    tweets = read_db_tweets()
    assert '562880888909099008' in tweets[-1]

