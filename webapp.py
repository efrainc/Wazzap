#! /usr/bin/env python

import os
import logging
import json
import datetime
import psycopg2
from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory
from pyramid.view import view_config
from pyramid.events import NewRequest, subscriber
from waitress import serve
from contextlib import closing
from geopy.geocoders import Nominatim

from tweepy_inter import authorize
from tweepy_inter import fetch_user_statuses

here = os.path.dirname(os.path.abspath(__file__))

# DB_SCHEMA = """
# CREATE TABLE IF NOT EXISTS entries (
#     id serial PRIMARY KEY,
#     title VARCHAR (127) NOT NULL,
#     tweet TEXT NOT NULL,
#     venue VARCHAR (127) NOT NULL,
#     created TIMESTAMP NOT NULL
# )
# """

LOCAL_CREDENTIALS = 'dbname=webapp_original user=henryhowes password=admin'

DB_LOCALS_SCHEMA = """
CREATE TABLE IF NOT EXISTS locals (
    id serial PRIMARY KEY,

    venue VARCHAR(127) NOT NULL,
    screen_name VARCHAR(127) NOT NULL,
    address TEXT NOT NULL,
    lat NUMERIC NOT NULL,
    long NUMERIC NOT NULL
)
"""

READ_LOCALS_ENTRY = """
SELECT "id", "venue", "screen_name", "address", "lat", "long" FROM "locals"
"""

WRITE_LOCALS_ENTRY = """
INSERT INTO "locals" ("venue", "screen_name", "address", "lat", "long") VALUES(%s, %s, %s, %s, %s)
"""

FETCH_LOCALS_ID = """
SELECT "id" FROM "locals" WHERE screen_name = %s
"""

DB_TWEETS_SCHEMA = """
CREATE TABLE IF NOT EXISTS "tweets" (
    "id" serial PRIMARY KEY,

    "parent_id" INTEGER REFERENCES locals ON UPDATE NO ACTION ON DELETE NO ACTION,
    "author_handle" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "time" TIMESTAMP NOT NULL,
    "count" INTEGER NOT NULL
)
"""

GET_VENUE_ID = """
SELECT id FROM locals WHERE address = %s
"""

# {table from} {id to associate with}
READ_TWEETS = """
SELECT id, parent_id, author_handle, content, time FROM tweets WHERE parent_id = %s ORDER BY time DESC
"""

# {table name} {data from one tweet}
WRITE_TWEET = """
INSERT INTO tweets (parent_id, author_handle, content, time, count) VALUES(%s, %s, %s, %s, %s)
"""

# {table name} {content to match}
UPDATE_TWEET = """
UPDATE tweets SET count = count + 1 WHERE content = %s
"""


# INSERT_ENTRY = """
# INSERT INTO entries (title, text, created) VALUES (%s, %s, %s)
# """

SELECT_ENTRIES = """
SELECT id, title, tweet, created, venue FROM entries ORDER BY created DESC
"""


logging.basicConfig()
log = logging.getLogger(__file__)


@subscriber(NewRequest)
def open_connection(event):
    request = event.request
    settings = request.registry.settings
    request.db = connect_db(settings)
    request.add_finished_callback(close_connection)

# @view_config(route_name='home', renderer='string')
# def home(request):
#     return "Wazzapp v1.0"


def connect_db(settings):
    """Return a connection to the configured database"""
    return psycopg2.connect(settings['db'])


def close_connection(request):
    """close the database connection for this request

    If there has been an error in the processing of the request, abort any
    open transactions.
    """
    db = getattr(request, 'db', None)
    if db is not None:
        if request.exception is not None:
            db.rollback()
        else:
            db.commit()
        request.db.close()


def init_db():
    """Create database tables defined by DB_SCHEMA

    Warning: This function will not update existing table definitions
    """
    settings = {}
    settings['db'] = os.environ.get(
        'DATABASE_URL', LOCAL_CREDENTIALS)
    with closing(connect_db(settings)) as db:
        # db.cursor().execute(DB_SCHEMA)
        db.cursor().execute(DB_LOCALS_SCHEMA)
        db.cursor().execute(DB_TWEETS_SCHEMA)
        db.commit()


def setup_data_snapshot():
    """
    Set up database for interaction.
    """
    settings = {}
    settings['db'] = os.environ.get(
        'DATABASE_URL', LOCAL_CREDENTIALS)
    with closing(connect_db(settings)) as db:
        cursor = db.cursor()
        # Write venues to locals table
        # venue, screen_name, address, lat, long
        # json.loads(response.content, response.encoding)['results'][0]['geometry']['location']['lat']
        keyarena = ('Key Arena', 'KeyArenaSeattle', '305 Harrison Street, Seattle, WA 98109', 47.6219664, -122.3545531)
        neumos = ('Neumos', 'Neumos', '925 East Pike Street, Seattle, WA 98122', 47.613843, -122.319716)
        # moore = ('The Moore Theatre', '', '1932 2nd Ave, Seattle, WA 98101', 47.6117865, -122.3413842)
        paramount = ('Paramount Theatre', 'BroadwaySeattle', '911 Pine Street, Seattle, WA 98101', 47.61347929999999, -122.3317273)
        for info in [keyarena, neumos, paramount]:
            write_local(info, db)

        # Write tweets to tweets table
        # parent_id, author_handle, content, time, count
        for handle in ['KeyArenaSeattle', 'Neumos', 'BroadwaySeattle']:
            pull_tweets(handle, db)


def write_local(local_info_tuple, connection):
    cursor = connection.cursor()
    cursor.execute(WRITE_LOCALS_ENTRY, local_info_tuple)
    connection.commit()


def pull_tweets(target_twitter_handle, connection):
    cursor = connection.cursor()
    cursor.execute(FETCH_LOCALS_ID, (target_twitter_handle,))
    refer = cursor.fetchone()[0]
    results = fetch_user_statuses(authorize(), target_twitter_handle, reference=refer)
    cursor.executemany(WRITE_TWEET, results)
    connection.commit()



# def write_entry(request):
#     """write a single entry to the database"""
#     title = request.params.get('title', None)
#     text = request.params.get('tweet', None)
#     created = datetime.datetime.utcnow()
#     request.db.cursor().execute(INSERT_ENTRY, [title, text, created])


@view_config(route_name='home', renderer='templates/base.jinja2')
def geo_json(request):
    """return a list of all entries as dicts"""
    cursor = request.db.cursor()
    cursor.execute(READ_TWEET, (1,))  # TODO: retrieving table id for a venue

    keys = ('id', 'parent_id', 'author_handle', 'content', 'time')
    entries = [dict(zip(keys, row)) for row in cursor.fetchall()]
    return {'entries': entries}


@view_config(route_name='gettweets', renderer='json')
def get_tweets_from_db(request):
    cursor = request.db.cursor()
    cursor.execute(GET_VENUE_ID, (request.params.get('address', None), ))
    venue_id = cursor.fetchone()
    cursor.execute(READ_TWEETS, venue_id)
    keys = ('id', 'parent_id', 'author_handle', 'content', 'time', 'count')
    tweets = [dict(zip(keys, row)) for row in cursor.fetchall()]
    for tweet in tweets:
        time_since = (datetime.datetime.now() - tweet['time']).seconds / 3600
        tweet['content'] = tweet['content'].encode('utf-8')
        tweet['time'] = "{} hours ago".format(time_since)
    return {'tweets': tweets}


def main():
    """Create a configured wsgi app"""
    settings = {}
    settings['reload_all'] = os.environ.get('DEBUG', True)
    settings['debug_all'] = os.environ.get('DEBUG', True)
    settings['db'] = os.environ.get(
        'DATABASE_URL', LOCAL_CREDENTIALS)
    # secret value for session signing:
    secret = os.environ.get('JOURNAL_SESSION_SECRET', 'itsaseekrit')
    session_factory = SignedCookieSessionFactory(secret)
    # configuration setup
    config = Configurator(
        settings=settings,
        session_factory=session_factory
    )
    config.include('pyramid_jinja2')
    config.add_route('home', '/')
    config.add_route('gettweets', '/gettweets')
    config.add_static_view('static', os.path.join(here, 'static'))
    config.scan()
    app = config.make_wsgi_app()
    return app


if __name__ == '__main__':
    app = main()
    port = os.environ.get('PORT', 8000)
    serve(app, host='127.0.0.1', port=port)
