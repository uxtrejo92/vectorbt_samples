import vectorbt as vbt
import pandas as pd
import numpy as np
from pathlib import Path
import os
from get_price import get_price_data
from indicators import range_filter

def combine_signals(long, short):
    count = 0
    index = 0
    l = []
    s = []
    for x in np.nditer(long):
        if count == 0:
            count += 1
            l.append(0)
            pre_value = x
        elif x == pre_value:
            pre_value = x
            count += 1
            l.append(0)
        else:
            pre_value = x
            count += 1
            if x == 1:
                if x not in l:
                    l.append(int(x))
                    index = count
                elif x in l:
                    validation_list = l[index:]
                    if -1 in validation_list:
                        l.append(int(x))
                        index = count
                    else:
                        l.append(0)
            else:
                l.append(int(x))
    count = 0
    index = 0
    for x in np.nditer(short):
        if count == 0:
            count += 1
            s.append(0)
            pre_value = x
        elif x == pre_value:
            pre_value = x
            count += 1
            s.append(0)
        else:
            pre_value = x
            count += 1
            if x == 2:
                if x not in s:
                    s.append(int(x))
                    index = count
                elif x in s:
                    validation_list = s[index:]
                    if -2 in validation_list:
                        s.append(int(x))
                        index = count
                    else:
                        s.append(0)
            else:
                s.append(int(x))
    return l, s

def produce_signal(entry_price, close_price, _ma_short, _ma_long):
    # Signal - value of 1 to be a buy, value of 0 is neutral not sell NOR buy, and a value of -1 to close position.
    long = np.where((_ma_short > _ma_long) & (entry_price > close_price)
                    , 1, 0)
    long = np.where((_ma_short < _ma_long), -1, long)
 # Signal - value of 2 to be a sell, value of 0 is neutral not buy NOR sell, and a value of -2 to close position.
    short = np.where((_ma_short < _ma_long) & (entry_price < close_price)
                     , 2, 0)
    short = np.where(_ma_short > _ma_long, -2, short)

    return combine_signals(long, short)

def customer_indicator(close, entry, ma_short, ma_long,):
    EMA = vbt.pandas_ta('EMA')
    _ma_short = EMA.run(close, ma_short).ema.values
    _ma_long = EMA.run(close, ma_long).ema.values
    entry_price = entry.to_numpy()
    close_price = close.to_numpy()
    return produce_signal(entry_price, close_price, _ma_short, _ma_long)


# Custome Indicator Instance - 
ind = vbt.IndicatorFactory(
    class_name="MovingAverage_Signal",
    short_name="MA_Indicator",
    input_names=["close", 'entry'],
    param_names=["ma_short", "ma_long"],
    output_names=["long", "short"],
).from_apply_func(
    customer_indicator,
    ma_short=20,
    ma_long=50,
    keep_pd=True,
)

stocks = ['TSLA']
timeframe = '1D'
fullday = True
for stock in stocks:
    high_price, low_price, close_price, start_time, end_time, ticker_price = get_price_data(
        stock, timeframe=timeframe, fullday=fullday)

    lowercase_columns = [col.lower().strip() for col in ticker_price.columns]
    ticker_price.columns = lowercase_columns
    entry_price = range_filter(ticker_price, range_qty=2.618)['rf']

    args = ["ma_short", "ma_long"]

    res = ind.run(
        close=close_price,
        entry = entry_price,
        ma_short=[20],
        ma_long=[50],
        param_product=True)

    entries = res.long.values == 1
    exits = res.long.values == -1
    short_entries = res.short.values == 2
    short_exits = res.short.values == -2

    # 0.01 = 1%, 0,0025 =  0.25%
    pf_kwargs = dict(size=np.inf, freq=timeframe)
    pf = vbt.Portfolio.from_signals(
        close_price,
        entries=entries,
        exits=exits,
        short_entries=short_entries,
        short_exits=short_exits,
        direction=vbt.portfolio.enums.Direction.Both,
        upon_stop_exit=vbt.portfolio.enums.StopExitMode.Close,
        upon_long_conflict=vbt.portfolio.enums.ConflictMode.Opposite,
        upon_short_conflict=vbt.portfolio.enums.ConflictMode.Opposite,
        upon_dir_conflict=vbt.portfolio.enums.DirectionConflictMode.Opposite,
        upon_opposite_entry=vbt.portfolio.enums.OppositeEntryMode.Reverse,
        stop_exit_price=vbt.portfolio.enums.StopExitPrice.Close,
        ** pf_kwargs
    )

    stats = pd.DataFrame(pf.stats())

    returns = pf._metrics

    df = stats.T
    df['Symbol'] = stock
    df['timeframe'] = timeframe
    df['st_tp'] = False
    df = df.drop(columns=['Start', 'End'])
    param_names = res.param_names
    for p in param_names:
        for attr, value in res.__dict__.items():
            found = False
            if p in attr:
                df[p] = value
                found = True
            if found:
                break

    for key in pf_kwargs:
        df[key] = pf_kwargs[key]

    file_name = os.path.basename(__file__)
    file_name = file_name.split('.')[0]

    path = f'Results/Retuns_result_{file_name}_fullday_{fullday}.csv'
    if os.path.isfile(path):
        df.to_csv(path, mode='a', header=False)
    else:
        df.to_csv(path, index=True)

    print(stock)
    pf.plot().show()
    print(file_name)
