import hmac
import requests
from requests import request
import pandas as pd

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
    if exchange == 'FTX':
        if end_ts == None:
            historical = ftxcall('get', f'/markets/{pair}/candles?resolution={resolution}&start_time={start_ts}')
        else:
            historical = ftxcall('get', f'/markets/{pair}/candles?resolution={resolution}&start_time={start_ts}&end_time={end_ts}')
        historical = pd.DataFrame(historical['result'])
        #historical.drop(['startTime'], axis = 1, inplace=True)
        historical['time'] = pd.to_datetime(historical['time'], unit='ms')
        historical.set_index('time', inplace=True)
        return historical

