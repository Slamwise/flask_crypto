from re import T
import requests
from requests import request
import pandas as pd
from datetime import datetime
import time

def ftxcall(method, endpoint):
    method = method.upper()
    url = 'https://ftx.com/api'
    response = request(method, url+endpoint)
    return response.json()

def bybcall(method, endpoint):
    method = method.upper()
    url = 'https://api.bybit.com'
    response = request(method, url+endpoint)
    return response.json()
  
def get_price(pair, start_ts, end_ts = None, resolution = '300', exchange = 'FTX'):

    intervals =  {15:3600, 60:86400, 300:86400, 900:86400, 3600:86400*5, 14400:86400*5, 86400:86400*10, 7*86400:86400*30, 30*86400:86400*365}
    window = intervals[int(resolution)]

    if end_ts == None:
        end_ts = int(datetime.utcnow().timestamp())

    if exchange == 'FTX':
        # If time period is too large, perform multiple calls:
        if (end_ts - start_ts) > window:
            time_list = [time for time in range(start_ts, end_ts, window)]

            if time_list[-1] != end_ts:
                time_list.append(end_ts)
            dflist = []

            for idx, t in enumerate(time_list):
                if idx+1 != len(time_list):
                    call = ftxcall('get', f'/markets/{pair}/candles?resolution={resolution}&start_time={t}&end_time={time_list[idx+1]}')
                    df = pd.DataFrame(call['result'])
                    df['time'] = pd.to_datetime(df['time'], unit='ms')
                    df.set_index('time', inplace=True)
                    dflist.append(df)
                    print(f'Fetched df {idx}/{len(time_list)-1}')
                    time.sleep(0.1)  

            historical = pd.concat(dflist)
            return historical

        else:    
            historical = ftxcall('get', f'/markets/{pair}/candles?resolution={resolution}&start_time={start_ts}&end_time={end_ts}')
            historical = pd.DataFrame(historical['result'])
            #historical.drop(['startTime'], axis = 1, inplace=True)
            historical['time'] = pd.to_datetime(historical['time'], unit='ms')
            historical.set_index('time', inplace=True)
            return historical

