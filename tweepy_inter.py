import tweepy


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


def fetch_user_statuses(api, name=None, how_many_tweets=50):
    """
    Return a list of timeline tweet content for a given user.
    """
    tweets = api.user_timeline(screen_name=name, count=how_many_tweets)
    content = []
    for tweet in tweets:
        content.append(repr(tweet.content))
    return content
