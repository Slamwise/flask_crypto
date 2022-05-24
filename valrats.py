import data
import time
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots


show_relative_volume_gainers = False
show_highest_perp_volume = False
show_assets_meeting_criteria = True
#criteria:
rel_vol_threshold = 1.5       # Filters out assets under this value
daily_gain_threshold = 1.1  # Filters out assets that have moved greater than this amount since one day ago.

    start_ts = date_to_seconds(start_str)
    # if an end time was not passed we need to use now
    if end_str is None:
        end_str = 'now UTC'
        end_ts = date_to_seconds(end_str)
    else:
      end_ts = date_to_seconds(end_str)

    if exchange == 'kucoin':
      # init our array for klines
      klines = []
      client = Client("", "", "")
      kline_res = client.get_kline_data(symbol, interval, start_ts, end_ts)

    if exchange == 'ftx':

      #Request
      historical = requests.get(f'https://ftx.com/api/markets/{symbol}/candles?resolution={units[interval]*60}&start_time={start_ts}&end_time={end_ts}').json()
      #print(historical)
      historical = pd.DataFrame(historical['result'])
      historical.drop(['startTime'], axis = 1, inplace=True)
      historical['time'] = pd.to_datetime(historical['time'], unit='ms')
      historical.rename(columns={'time': 'Time', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
      
      kline_res = historical
      del historical

      return kline_res

    # check if we got a result
    if 't' in kline_res and len(kline_res['t']):
        # now convert this array to OHLCV format and add to the array
        for i in range(1, len(kline_res['t'])):
            klines.append((
                kline_res['t'][i],
                kline_res['o'][i],
                kline_res['h'][i],
                kline_res['l'][i],
                kline_res['c'][i],
                kline_res['v'][i]
            ))
    for i in kline_res:
      i[0] = int(i[0])
      i[1] = float(i[1])
      i[2] = float(i[2])
      i[3] = float(i[3])
      i[4] = float(i[4])
      i[5] = float(i[5])
      i[6] = float(i[6])

    #print(kline_res)
    # finally return our converted klines
    #df = pd.DataFrame(klines, columns=['Open','High','Low','Close','Volume'])
    return kline_res

if in_kucoin == True:
  client = Client("", "", "")
  kusymbols = []
  symbols = client.get_symbols()
  for i in symbols:
    if i['symbol'].split('-')[1] == 'USDT':
      kusymbols.append(i['symbol'].split('-')[0])
  print(kusymbols)

def ftxrequest(type, request):
  if type == 'get':
    response = requests.get(f'https://ftx.com/api/{request}').json()
    return response['result']

print(ftxrequest('get', 'markets/WAVES-PERP')['quoteVolume24h'])
print(ftxrequest('get', 'markets/WAVES/USD')['quoteVolume24h'])

perpdict = {}
spotdict = {}
bothdict = {}

assets = ftxrequest('get', 'markets')
for i in assets:
  if 'PERP' in i['name']:
    name = i['name'].split('-')[0]
    perpdict[name] = i['quoteVolume24h']
  if '/USD' in i['name']:
    name = i['name'].split('/')[0]
    spotdict[name] = i['quoteVolume24h']

for key,value in perpdict.items():
  try:
    bothdict[key] = value + spotdict[key]
  except:
    continue

pdf = pd.DataFrame(perpdict.items(), columns=['asset', 'volume'])
pdf.sort_values(by=['volume'], ascending=False, inplace=True)

sdf = pd.DataFrame(spotdict.items(), columns=['asset', 'volume'])
sdf.sort_values(by=['volume'], ascending=False, inplace=True)

bdf = pd.DataFrame(bothdict.items(), columns=['asset', 'volume'])
bdf.sort_values(by=['volume'], ascending=False, inplace=True)

#print(pdf.head(20))
#print(sdf.head(20))
#print(bdf.head(20))

top200 = []
sorted = []
for i in bdf.head(100).values.tolist():
  top200.append(i[0])
for i in bdf.values.tolist():
  sorted.append(i[0])

print(top200)

def get_daily_data(exchange, asset, lookback):
  df = pd.DataFrame(get_historical_klines_tv(exchange, asset, '1day', f'{lookback} day ago UTC'), 
                            columns=['Time','Open','High','Low','Close','Amount','Volume'])
  return df
def get_data(exchange, asset, unit, lookback, time_period):
  df = pd.DataFrame(get_historical_klines_tv(exchange, asset, unit, f'{lookback} {time_period} ago UTC'), 
                            columns=['Time','Open','High','Low','Close','Amount','Volume'])
  return df

perpavgdict = {}
spotavgdict = {}
for i in top200:
  try:
    df = get_daily_data('ftx', i + '-PERP', 30)
    avg_vol = df[:-1]['Volume'].mean()
    perpavgdict[i] = avg_vol
  except:
    continue
  try:
    df = get_daily_data('ftx', i + '/USD', 30)
    avg_vol = df[:-1]['Volume'].mean()
    spotavgdict[i] = avg_vol
  except:
    continue
print(perpavgdict)
print(spotavgdict)

pct_gains_perp = {}
pct_gains_spot = {}

for key,value in perpavgdict.items():
  new_key = key.split('-')[0]
  pct_gain = (perpdict[new_key]/value)*100 - 100
  pct_gains_perp[key] = pct_gain

for key,value in spotavgdict.items():
  new_key = key.split('/')[0]
  if value != 0:
    pct_gain = (spotdict[new_key]/value)*100 - 100
    pct_gains_spot[key] = pct_gain

print(pct_gains_perp)
print(pct_gains_spot)

adf = pd.DataFrame(pct_gains_perp.items(), columns=['asset', 'pct_gain'])
adf.sort_values(by=['pct_gain'], ascending=False, inplace=True)
adf.head(20)

#Sorted by biggest relative volume gainers
if show_relative_volume_gainers == True:
  fig = make_subplots()
  for row, value in adf[0:10].iterrows():
    try:
      perp_df = get_data('ftx', value['asset'], '5min', 3, 'day')
      spot_df = get_data('ftx', value['asset'].split('-')[0]+'/USD', '5min', 3, 'day')

      perp_df['rel_vol'] = perp_df['Volume'].rolling(288).sum() / perpavgdict[value['asset']]
      spot_df['rel_vol'] = spot_df['Volume'].rolling(288).sum() / spotavgdict[value['asset'].split('-')[0]+'/USD']

      perp_df['rel_vol_ratio'] = spot_df.rel_vol / perp_df.rel_vol

      fig.add_trace(
          go.Scatter(name=value['asset'].split('-')[0], mode='lines', x=perp_df.index, y=perp_df.rel_vol_ratio))
    except:
      continue

#Sorted by top PERP volume Top 20
if show_highest_perp_volume == True:
  fig = make_subplots()
  for i in top200[:19]:
    try:
      perp_df = get_data('ftx', i+'-PERP', '5min', 3, 'day')
      spot_df = get_data('ftx', i+'/USD', '5min', 3, 'day')

      perp_df['rel_vol'] = perp_df['Volume'].rolling(288).sum() / perpavgdict[i]
      spot_df['rel_vol'] = spot_df['Volume'].rolling(288).sum() / spotavgdict[i]

      perp_df['rel_vol_ratio'] = spot_df.rel_vol / perp_df.rel_vol

      fig.add_trace(
          go.Scatter(name=i, mode='lines', x=perp_df.index, y=perp_df.rel_vol_ratio))
    except:
      continue

#Sorted by criteria
show_assets_meeting_criteria = True
if show_assets_meeting_criteria == True:
  fig = make_subplots()
  for i in sorted:
    try:
      perp_df = get_data('ftx', i+'-PERP', '5min', 3, 'day')
      spot_df = get_data('ftx', i+'/USD', '5min', 3, 'day')

      perp_df['rel_vol'] = perp_df['Volume'].rolling(288).sum() / perpavgdict[i]
      spot_df['rel_vol'] = spot_df['Volume'].rolling(288).sum() / spotavgdict[i]

      perp_df['rel_vol_ratio'] = spot_df.rel_vol / perp_df.rel_vol

      # Find Assets with ratios >= 3 that haven't moved much yet.
      if perp_df.iloc[-1:].rel_vol_ratio.item() >= rel_vol_threshold:
        if perp_df.iloc[-1:].Close.item()/perp_df.iloc[576].Close.item() <= daily_gain_threshold:
          if in_kucoin == True:
            fig.add_trace(
                go.Scatter(name=i, mode='lines', x=perp_df.index, y=perp_df.rel_vol_ratio))
            print(f'{i} : {perp_df.iloc[-1:].rel_vol_ratio.item()}')
          else:
            fig.add_trace(
              go.Scatter(name=i, mode='lines', x=perp_df.index, y=perp_df.rel_vol_ratio))
            print(f'{i} : {perp_df.iloc[-1:].rel_vol_ratio.item()}')          
    except:
      continue

fig.update_layout(yaxis_range=[0,4])
fig.update_layout(xaxis_range=[287, 287*3])
fig.show()