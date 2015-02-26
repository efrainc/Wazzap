#! /usr/bin/env python

from tweepy_inter import authorize, fetch_user_statuses
from webapp import closing
from webapp import connect_db
import os
from webapp import pull_handle


def update_tweets_db():
    login = authorize()
    settings = {}
    settings['db'] = os.environ.get('DATABASE_URL',
                     'dbname=test_wazzap user=efrain-petercamacho')
    with closing(connect_db(settings)) as db:
        handlers_list = pull_handle(db)
        for handel in handlers_list:
            fetch_user_statuses(login, handel)


if __name__=='__main__':
    update_tweets_db()
