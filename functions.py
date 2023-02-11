import vectorbt as vbt
import datetime
import pandas as pd
from pathlib import Path
from datetime import timedelta, date
import calendar
import sys



tz = 'America/New_York'
fullday = True
now = datetime.datetime.now()
month = now.strftime("%B")
today = datetime.datetime.now().date()
date_format = today.strftime("%m/%d/%Y")

def weekdays_in_month(year=2023 or int, month=str):
    last_day = calendar.monthrange(year, month)[1]
    dates = pd.date_range(start=f'{year}-{month}-01', end=f'{year}-{month}-{last_day}', freq='D')
    mondays = dates[dates.weekday == 0]
    fridays = dates[dates.weekday == 4]
    return mondays.tolist(), fridays.tolist()

def add_moretime():
    mult_arr = [7, 7, 7]
    start_date = []
    end_date = []
    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=7)
    start_date.append(start)
    end_date.append(end)
    for i in mult_arr:
        start = start - datetime.timedelta(days=i)
        end = start + timedelta(days=i)
        start_date.append(start)
        end_date.append(end)
    start_date.sort()
    end_date.sort()
    return start_date, end_date

def get_folder(time_frame='1m'):
    if time_frame == '1m':
        folder = f'/Users/urieltrejo/Documents/Vector_BT/Stock_Backtests/Minute_Timeframe/'
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=7)
        return folder, end_date, start_date
    elif time_frame == '1h':
        folder = f'/Users/urieltrejo/Documents/Vector_BT/Stock_Backtests/Hour_Timeframe/'
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=90)
        return folder, end_date, start_date
    elif time_frame == '1D':
        folder = f'/Users/urieltrejo/Documents/Vector_BT/Stock_Backtests/Day_Timeframe/'
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=600)
        return folder, end_date, start_date

def get_folder_two(time_frame='1D'):
    if time_frame == '1m':
        folder = f'/Users/urieltrejo/Documents/Vector_BT/Stock_Backtests/Minute_Timeframe/'
        return folder
    elif time_frame == '1h':
        folder = f'/Users/urieltrejo/Documents/Vector_BT/Stock_Backtests/Hour_Timeframe/'
        return folder
    elif time_frame == '1D':
        folder = f'/Users/urieltrejo/Documents/Vector_BT/Stock_Backtests/Day_Timeframe/'
        return folder

def get_asset(time_frame='1m', stock=str, month=str):
    months_dict = {'January':1, 'February':2, 'March':3, 'April':4, 'May':5, 'June':6, 'July':7, 'August':8, 'September':9, 'October':10, 'November':11, 'December':12}
    month_int = months_dict[month]
    folder, end_date, start_date = get_folder(time_frame)
    try:
        if time_frame in ['1h', '1D']:
            stock_data = vbt.YFData.download(
                stock,
                start=start_date,
                end=end_date,
                interval=time_frame)
            print(stock_data)
        if time_frame == '1m':
            data = []
            mondays, fridays = weekdays_in_month(2022, month_int)
            print(mondays)
            print(fridays)
            for x in range(0, 4):
                start = pd.to_datetime(mondays[x])
                end = pd.to_datetime(fridays[x])
                print(start, end)
                if start > end:
                    if len(mondays) < len(fridays):
                        fridays.remove(fridays[0])
                        print(fridays)
                        end = pd.to_datetime(fridays[x])
                stock_data = vbt.YFData.download(
                    stock,
                    missing_index='drop',
                    start=start,
                    end=end,
                    interval=time_frame).get()
                data.append(stock_data)
            stock_data = pd.concat(data)
            stock_data = stock_data.tz_convert(tz)
            copy = stock_data.reset_index()
            copy['time'] = copy['Datetime'].dt.time
            if fullday:
                start_time = copy['time'] > pd.Timestamp(
                    '9:30').time()
                end_time = copy['time'] < pd.Timestamp('15:59').time()
                stock_data['start_time'] = start_time.values
                stock_data['end_time'] = end_time.values
            else:
                start_time = copy['time'] > pd.Timestamp(
                    '10:00').time()
                end_time = copy['time'] < pd.Timestamp('15:45').time()
                stock_data['start_time'] = start_time.values
                stock_data['end_time'] = end_time.values

        if time_frame in ['1h', '1D']:
            filepath = Path(folder + f'data_{stock}_timeframe_{time_frame}_{month}.csv')
            stock_data.to_csv(filepath)
        else:
            filepath = Path(folder + f'data_{stock}_timeframe_{time_frame}_{fullday}_{month}.csv')
            stock_data.to_csv(filepath)
    except Exception as e:
        print(e)
        print('Cannot retrieve stock data')
        sys.exit()

def get_asset_two(time_frame='1m', stock=str, start_date=date, end_date=date):
    folder = get_folder_two(time_frame)
    try:
        if time_frame in ['1h', '1D']:
            stock_data = vbt.YFData.download(
                stock,
                start=start_date,
                end=end_date,
                interval=time_frame)
            print(stock_data)
        if time_frame == '1m':
            stock_data = vbt.YFData.download(
                stock,
                missing_index='drop',
                start=start_date,
                end=end_date,
                interval=time_frame).get()
            stock_data = stock_data.tz_convert(tz)
            copy = stock_data.reset_index()
            copy['time'] = copy['Datetime'].dt.time
            if fullday:
                start_time = copy['time'] > pd.Timestamp(
                    '9:30').time()
                end_time = copy['time'] < pd.Timestamp('15:59').time()
                stock_data['start_time'] = start_time.values
                stock_data['end_time'] = end_time.values
            else:
                start_time = copy['time'] > pd.Timestamp(
                    '10:00').time()
                end_time = copy['time'] < pd.Timestamp('15:45').time()
                stock_data['start_time'] = start_time.values
                stock_data['end_time'] = end_time.values

        if time_frame in ['1h', '1D']:
            filepath = Path(folder + f'data_{stock}_timeframe_{time_frame}_specific_time.csv')
            stock_data.to_csv(filepath)
        else:
            filepath = Path(folder + f'data_{stock}_timeframe_{time_frame}_specific_time.csv')
            stock_data.to_csv(filepath)
    except Exception as e:
        print(e)
        print('Cannot retrieve stock data')
        sys.exit()