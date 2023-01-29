import pandas as pd
from pathlib import Path
from functions import get_asset
import datetime

now = datetime.datetime.now()
month = now.strftime("%B")


def get_price_data(ticker, timeframe='1m', fullday=False, month='December' or str):

    if timeframe == '1m':
        folder = 'Minute_Timeframe'
    elif timeframe == '1h':
        folder = 'Hour_Timeframe'
    elif timeframe == '1D':
        folder = 'Day_Timeframe'
    try:
        if timeframe in ['1h', '1D']:
           path = Path(f'/Users/urieltrejo/Documents/Vector_BT/Stock_Backtests/{folder}/data_{ticker}_timeframe_{timeframe}_{month}.csv')
           ticker_price = pd.read_csv(path)
           print(ticker_price)
           low_price = ticker_price.get('Low')
           close_price = ticker_price.get('Close')
           high_price = ticker_price.get('High')
           start_time = ticker_price.get('start_time')
           end_time = ticker_price.get('end_time')
           return high_price, low_price, close_price, start_time, end_time, ticker_price
        else:
            path = Path(f'/Users/urieltrejo/Documents/Vector_BT/Stock_Backtests/{folder}/data_{ticker}_timeframe_{timeframe}_{fullday}_{month}.csv')
            ticker_price = pd.read_csv(path)
            print(ticker_price)
            low_price = ticker_price.get('Low')
            close_price = ticker_price.get('Close')
            high_price = ticker_price.get('High')
            start_time = ticker_price.get('start_time')
            end_time = ticker_price.get('end_time')
            return high_price, low_price, close_price, start_time, end_time, ticker_price
    except Exception as e:
        print(e)
        print('Trying to get data for {}'.format(ticker))
        get_asset(time_frame=timeframe, stock=ticker, month=month)
        high_price, low_price, close_price, start_time, end_time, ticker_price = get_price_data(ticker, fullday=fullday, month=month)
        return high_price, low_price, close_price, start_time, end_time, ticker_price


