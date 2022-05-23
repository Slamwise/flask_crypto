import tweepy
from tweepy.auth import OAuthHandler
import os
import pandas as pd
import numpy as np
import time
import sec

def get_whaletrades(count, coin):
    auth = OAuthHandler(sec.consumer_key, sec.consumer_secret)
    auth.set_access_token(sec.access_token, sec.access_token_secret)
    api = tweepy.API(auth,wait_on_rate_limit=True)

    #Get tweets
    username = 'WhaleTrades'
    try:     
        # Creation of query method using parameters
        tweets = tweepy.Cursor(api.user_timeline,id=username).items(count)
        
        # Pulling information from tweets iterable object
        tweets_list = [[tweet.created_at, tweet.id, tweet.text] for tweet in tweets]
        
        # Creation of dataframe from tweets list
        # Add or remove columns as you remove tweet information
        tweets_df = pd.DataFrame(tweets_list)

    except BaseException as e:
        print('failed on_status,',str(e))
        time.sleep(3)

    #Parse tweets
    prints = []
    for i in tweets_list:
        if f"${coin}" in i[2]:
            value = int(i[2].splitlines()[0].split()[0][3:].replace(',',''))
            side = i[2].splitlines()[0].split()[2]
            price = float(i[2].splitlines()[0].split()[3].replace('@','').replace('$','').replace(',',''))
            when = i[0]
            if side != 'LONGED':
                prints.append((when, -1*value, side, price))
            else:
                prints.append((when, value, side, price))

    tdf = pd.DataFrame(prints, columns=['Date','Size','Side','Price'])
    
    return tdf