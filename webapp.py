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

here = os.path.dirname(os.path.abspath(__file__))

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id serial PRIMARY KEY,
    title VARCHAR (127) NOT NULL,
    tweet TEXT NOT NULL,
    venue VARCHAR (127) NOT NULL,
    created TIMESTAMP NOT NULL
)
"""

INSERT_ENTRY = """
INSERT INTO entries (title, text, created) VALUES (%s, %s, %s)
"""

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
        'DATABASE_URL', 'dbname=webapp_original user=efrain-petercamacho'
    )
    with closing(connect_db(settings)) as db:
        db.cursor().execute(DB_SCHEMA)
        db.commit()

def write_entry(request):
    """write a single entry to the database"""
    title = request.params.get('title', None)
    text = request.params.get('tweet', None)
    created = datetime.datetime.utcnow()
    request.db.cursor().execute(INSERT_ENTRY, [title, text, created])


@view_config(route_name='home', renderer='templates/base.jinja2')
def read_entries(request):
    """return a list of all entries as dicts"""
    cursor = request.db.cursor()
    cursor.execute(SELECT_ENTRIES)
    keys = ('id', 'title', 'tweet', 'created', 'venue')
    entries = [dict(zip(keys, row)) for row in cursor.fetchall()]
    return {'entries': entries}

def main():
    """Create a configured wsgi app"""
    settings = {}
    settings['reload_all'] = os.environ.get('DEBUG', True)
    settings['debug_all'] = os.environ.get('DEBUG', True)
    settings['db'] = os.environ.get(
    'DATABASE_URL', 'dbname=webapp_original user=efrain-petercamacho'
    )
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
    config.add_static_view('static', os.path.join(here, 'static'))
    config.scan()
    app = config.make_wsgi_app()
    return app


if __name__ == '__main__':
    app = main()
    port = os.environ.get('PORT', 5000)
    serve(app, host='0.0.0.0', port=port)