import pandas as pd
import numpy as np
from data import get_price, bybcall
from twitter import get_whaletrades
import time
from datetime import datetime
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from flask import Flask, render_template, Markup
import os.path
import os

app = Flask(__name__, static_url_path='/static')

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route("/whaletrades")
@app.route('/whaletrades/<coin>')
def whaletrades(coin=None):
    # // Fetching data:
    if os.path.isfile(f'./cache/{coin}ldf.pkl'):
        tdf = pd.read_pickle(f'./cache/{coin}tdf.pkl')
        ldf = pd.read_pickle(f'./cache/{coin}ldf.pkl')
        sdf = pd.read_pickle(f'./cache/{coin}sdf.pkl')
    else:
        tdf = get_whaletrades(500, coin)
        tdf.to_pickle(f'./cache/{coin}tdf.pkl')

        ldf = tdf.where(tdf.Size > 0).dropna()
        ldf.to_pickle(f'./cache/{coin}ldf.pkl')

        sdf = tdf.where(tdf.Size < 0).dropna()
        sdf.to_pickle(f'./cache/{coin}sdf.pkl')

    if os.path.isfile(f'./cache/{coin}hist.pkl'):
        historical = pd.read_pickle(f'./cache/{coin}hist.pkl')
    else:
        start_ts = int(tdf['Date'].tail(1).item().timestamp()) - 300
        historical = get_price(f'{coin}/USD', start_ts, int(datetime.utcnow().timestamp()))
        historical.to_pickle(f'./cache/{coin}hist.pkl')
    
    daily_info = bybcall('get', f'/v2/public/tickers?symbol={coin}USD')['result'][0]

    # // Plot data:

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Candlestick(name='Price', x=historical.index, open=historical.open, high=historical.high, low=historical.low, close=historical.close)
        )
    fig.add_trace(
        go.Scatter(name='Longs', mode='markers', hovertext=ldf.Size.map('${:,.2f}'.format), hoverinfo='text+x', x=ldf.Date, y=ldf.Price, marker = dict(size=ldf.Size/700000, color = 'Green'))
        )
    fig.add_trace(
        go.Scatter(name='Shorts', mode='markers', hovertext=sdf.Size.map('${:,.2f}'.format), hoverinfo='text+x', x=sdf.Date, y=sdf.Price, marker = dict(size=-1*sdf.Size/700000, color = 'Red'))
        )
    fig.add_trace(
        go.Scatter(name='CVD', x=tdf.iloc[::-1].Date, y=tdf.iloc[::-1].Size.cumsum(), line=dict(color='red', width=2)),
        secondary_y=True
        )
    # Add figure title
    fig.update_layout(title_text=f'{coin}/USD')
    # Set x-axis title
    fig.update_xaxes(title_text="Time")
    # Set y-axes titles
    fig.update_yaxes(title_text="Price", secondary_y=False, side='right')
    fig.update_yaxes(title_text="CVD", secondary_y=True, side='left')
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    last_price = float(daily_info['last_price'])
    prev_price_24h = float(daily_info['prev_price_24h'])

    fig_html = fig.to_html()

    context = {"showgraph": "showgraph"}
    return render_template('chart.html', chart_placeholder=Markup(fig_html))

if __name__ == 'app':
    print('running')
    try:
        dir = './cache'
        for f in os.listdir(dir):
            os.remove(os.path.join(dir, f))
    except:
        print('cache remove failed')
        pass   
    app.run(debug=True)