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

LOCAL_CREDENTIALS = 'dbname=postgres user=ubuntu password='

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
INSERT INTO "locals" ("venue", "screen_name", "address") VALUES(%s, %s, %s)
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
    "count" INTEGER NOT NULL,
    "status_id" INTEGER NOT NULL
)
"""

GET_VENUE_INFO = """
SELECT id, venue FROM locals WHERE address = %s
"""

# {table from} {id to associate with}
READ_TWEET = """
SELECT id, parent_id, author_handle, content, time FROM tweets WHERE parent_id = %s ORDER BY time DESC
"""

# {table name} {data from one tweet}
WRITE_TWEET = """
INSERT INTO tweets (parent_id, author_handle, content, time, count, status_id) VALUES(%s, %s, %s, %s, %s, %s)
"""

# {table name} {content to match}
UPDATE_TWEET = """
UPDATE tweets SET count = count + 1 WHERE content = %s
"""


# INSERT_ENTRY = """
# INSERT INTO entries (title, text, created) VALUES (%s, %s, %s)
# """

# SELECT_ENTRIES = """
# SELECT id, title, tweet, created, venue FROM entries ORDER BY created DESC
# """


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
    if os.environ.get('USER') == 'ubuntu':
        import secrets
        settings['db'] = secrets.dbase_connection()
    elif os.environ.get('USER') == 'JustinKan':
        settings['db'] = os.environ.get(
            'DATABASE_URL', 'dbname=postgres user=JustinKan')
    elif os.environ.get('USER') == 'efrain-petercamacho':
        settings['db'] = os.environ.get(
            'DATABASE_URL', 'dbname=postgres user=efrain-petercamacho')
    elif os.environ.get('USER') == 'henryhowes':
        settings['db'] = os.environ.get(
            'DATABASE_URL', 'dbname=webbapp_original user=henryhowes')
    elif os.environ.get('USERNAME') == 'jefimenko':
        settings['db'] = os.environ.get(
            'DATABASE_URL', 'dbname=postgres user=postgres password=admin')
    else:
        raise AttributeError('Not authorized to use database')
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
        # cursor = db.cursor()
        # Write venues to locals table
        # venue, screen_name, address, lat, long
        # json.loads(response.content, response.encoding)['results'][0]['geometry']['location']['lat']
        venue_list = []

        venue_list.append(('Key Arena', 'KeyArenaSeattle',
                           '305 Harrison Street, Seattle, WA 98109'))

        venue_list.append(('Neumos', 'Neumos',
                           '925 East Pike Street, Seattle, WA 98122'))

        venue_list.append(('Paramount Theatre', 'BroadwaySeattle',
                           '911 Pine Street, Seattle, WA 98101'))

        venue_list.append(('Fremont Brewing', 'fremontbrewing',
                           '1050 North 34th Street, Seattle, WA 98103'))

        venue_list.append(('Tractor Tavern', 'tractortavern',
                           '5213 Ballard Avenue Northwest, Seattle, WA 98107'))

        venue_list.append(('Nectar Lounge', 'NectarLounge',
                           '412 North 36th Street, Seattle, WA 98103'))

        venue_list.append(('The Triple Door', 'TheTripleDoor',
                           '216 Union Street, Seattle, WA 98101'))

        venue_list.append(('The Showbox', 'ShowboxPresents',
                           '1426 1st Avenue, Seattle, WA 98101'))

        venue_list.append(('The Crocodile', 'thecrocodile',
                           '2200 2nd Avenue, Seattle, WA 98121'))

        venue_list.append(('Central Cinema', 'CentralCinema',
                           '1411 21st Avenue, Seattle, WA 98122'))

        for venue in venue_list:
            write_local(venue, db)

        # Write tweets to tweets table
        # parent_id, author_handle, content, time, count
        for venue in venue_list:
            pull_tweets(venue[1], db)


def write_local(local_info_tuple, connection):
    cursor = connection.cursor()
    cursor.execute(WRITE_LOCALS_ENTRY, local_info_tuple)
    connection.commit()


def pull_tweets(target_twitter_handle, connection):
    cursor = connection.cursor()
    cursor.execute(FETCH_LOCALS_ID, (target_twitter_handle,))
    refer = cursor.fetchone()[0]
    results = fetch_user_statuses(
        authorize(), target_twitter_handle, reference=refer)
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
    cursor.execute(GET_VENUE_INFO, (request.params.get('address', None), ))
    venue_info = cursor.fetchone()
    cursor.execute(READ_TWEET, [venue_info[0]])
    keys = ('id', 'parent_id', 'author_handle', 'content', 'time', 'count', 'status_id')
    tweets = [dict(zip(keys, row)) for row in cursor.fetchall()]
    for tweet in tweets:
        time_since = int((
            datetime.datetime.utcnow() - tweet['time']).total_seconds() // 3600)
        tweet['content'] = tweet['content']
        tweet['time'] = "{} hours ago".format(time_since)
    return {'venue': venue_info[1], 'tweets': tweets}


def main():
    """Create a configured wsgi app"""
    settings = {}
    settings['reload_all'] = os.environ.get('DEBUG', True)
    settings['debug_all'] = os.environ.get('DEBUG', True)
    if os.environ.get('USER') == 'ubuntu':
        import secrets
        settings['db'] = secrets.dbase_connection()
    elif os.environ.get('USER') == 'JustinKan':
        settings['db'] = os.environ.get(
            'DATABASE_URL', 'dbname=postgres user=JustinKan')
    elif os.environ.get('USER') == 'efrain-petercamacho':
        settings['db'] = os.environ.get(
            'DATABASE_URL', 'dbname=postgres user=efrain-petercamacho')
    elif os.environ.get('USER') == 'henryhowes':
        settings['db'] = os.environ.get(
            'DATABASE_URL', 'dbname=webapp_original user=henryhowes')
    elif os.environ.get('USERNAME') == 'jefimenko':
        settings['db'] = os.environ.get(
            'DATABASE_URL', 'dbname=postgres user=postgres password=admin')
    else:
        raise AttributeError('Not authorized to use database')
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

DELETE_TWEETS = """
DELETE FROM tweets
"""


def clear_database(connection):
    cursor = connection.cursor()
    cursor.execute(DELETE_TWEETS)
    connection.commit()

if __name__ == '__main__':
    app = main()
    port = os.environ.get('PORT', 8000)
    serve(app, host='127.0.0.1', port=port)
