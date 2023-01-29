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


def produce_signal(supertd, start_time, end_time, _vhf_short_ma, _vhf_long_ma, _ma_short, _ma_long, vhf_threshold):
    # Signal - value of 1 to be a buy, value of 0 is neutral not sell NOR buy, and a value of -1 to close position.
    time = np.where((start_time == True) & (end_time == True), 1, 0)
    long = np.where((supertd == 1) & (_vhf_short_ma > _vhf_long_ma) & (_ma_short > _ma_long)
                    & (_vhf_short_ma > vhf_threshold) & (time == 1), 1, 0)
    long = np.where((time == 0) | (supertd == -1), -1, long)
    # Signal - value of 2 to be a sell, value of 0 is neutral not buy NOR sell, and a value of -2 to close position.
    short = np.where((supertd == -1) & (_vhf_short_ma > _vhf_long_ma) & (_ma_short < _ma_long)
                     & (_vhf_short_ma > vhf_threshold) & (time == 1), 2, 0)
    short = np.where((time == 0) | (supertd == 1), -2, short)

    return combine_signals(long, short)


def customer_indicator(close, high, low, start_time, end_time, atr_length, factor, vhf_val, ma_short, ma_long, vhf_short, vhf_long, vhf_threshold):
    SUPERTREND = vbt.pandas_ta('SUPERTREND')
    st = SUPERTREND.run(high, low, close, period=atr_length,
                        multiplier=factor).supertd
    VHF = vbt.pandas_ta('VHF')
    _vhf = VHF.run(close, period=vhf_val).vhf.values
    _vhf_short_ma = vbt.MA.run(_vhf, vhf_short).ma.values
    _vhf_long_ma = vbt.MA.run(_vhf, vhf_long).ma.values

    _ma_short = vbt.MA.run(close, ma_short).ma.values
    _ma_long = vbt.MA.run(close, ma_long).ma.values
    supertd = st.values
    start_time = start_time.to_numpy()
    end_time = end_time.to_numpy()
    return produce_signal(supertd, start_time, end_time, _vhf_short_ma, _vhf_long_ma, _ma_short, _ma_long, vhf_threshold)


ind = vbt.IndicatorFactory(
    class_name="Combination",
    short_name="comb",
    input_names=["close", "high", "low", 'start_time', "end_time"],
    param_names=["atr_length", "factor", "vhf_val", "ma_short", "ma_long", "vhf_short",
                 "vhf_long", "vhf_threshold"],
    output_names=["long", "short"],
).from_apply_func(
    customer_indicator,
    atr_length=10,
    factor=5,
    vhf_val=28,
    ma_short=20,
    ma_long=50,
    vhf_short=7,
    vhf_long=14,
    vhf_threshold=.25,
    keep_pd=True,
)

stocks = ['GOOG']
timeframe = '1m'
fullday = True
for stock in stocks:
    high_price, low_price, close_price, start_time, end_time, ticker_price = get_price_data(
        stock, timeframe=timeframe, fullday=fullday)
    args = ["atr_length", "factor", "vhf_val", "ma_short", "ma_long", "vhf_short",
            "vhf_long", "vhf_threshold"]

    res = ind.run(
        close=close_price,
        high=high_price,
        low=low_price,
        start_time=start_time,
        end_time=end_time,
        atr_length=[10],
        factor=[2.5],
        vhf_val=[56],
        ma_short=[9],
        ma_long=[28],
        vhf_short=[21],
        vhf_long=[28],
        vhf_threshold=[.2],
        param_product=True)

    entries = res.long.values == 1
    exits = res.long.values == -1
    short_entries = res.short.values == 2
    short_exits = res.short.values == -2

    lowercase_columns = [col.lower().strip() for col in ticker_price.columns]
    ticker_price.columns = lowercase_columns
    entry_price = range_filter(ticker_price, range_qty=2.6)['rf']

    # 0.01 = 1%, 0,0025 =  0.25%
    pf_kwargs = dict(size=np.inf, freq=timeframe, sl_stop=.006, tp_stop=.002)
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
