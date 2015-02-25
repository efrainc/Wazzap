import tweepy
import threading
import psycopg2
import re


def authorize():
    """
    Use OAuth to setup access token for the app.
    """
    auth = tweepy.OAuthHandler(
        'Xm4gPHD64LuLKJNam2aRbJhi9',
        'rZsFYrxsGfiq4TAQ2yKbtUBKeRhI7QnMLUxFGf0pI35DrZKDLH'
    )
    auth.set_access_token(
        '2489534185-wWhkpgFhDEodaaE73bL34JW9dlwG3ZtktQJA8xf',
        '5OewpVBuhQmyoh31EI4zOz2YJuFmycqPL1GiCGVlCDp4C'
    )

    return tweepy.API(auth)


def fetch_related_statuses(api, name, how_many_tweets=25):
    """
    Return a list of (user name, related tweet content).
    """
    pass


def write_data(tweets_list):
    with open('tweets.txt') as f:
        f.write(tweets_list)


def fetch_user_statuses(api, target_twitter_handle=None, reference=0, how_many_tweets=50):
    """
    Return a list of (user name, content, tweet time(gmt)).
    """
    tweets = api.user_timeline(screen_name=target_twitter_handle, count=how_many_tweets)
    content = []
    for tweet in tweets:
        # If retweeted, a tweet begins with 'RT @name:'
        if tweet.text.startswith(u'RT @'):
            author = re.compile(r'RT @\S+:').match(tweet.text).group()[4:-1]
        else:
            author = target_twitter_handle  # Venue twitter handle
        content.append(
            [reference, author, tweet.text.encode('utf-8'), tweet.created_at, 1]
        )
    return content
