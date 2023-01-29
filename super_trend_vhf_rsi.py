import vectorbt as vbt
import pandas as pd
import numpy as np
import os
from get_price import get_price_data

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
            s.append(int(x))
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


def produce_signal(supertd, start_time, end_time, _vhf_short_ma, _vhf_long_ma, _rsi_short, _rsi_long, rsi_thres_long, rsi_thres_short, short_mvg, long_mvg, vhf_threshold):
    # Signal - value of 1 to be a buy, value of 0 is neutral not sell NOR buy, and a value of -1 to close position.
    time = np.where((start_time == True) & (end_time == True), 1, 0)
    long = np.where((supertd == 1) & (_vhf_short_ma < _vhf_long_ma) & (_rsi_short > _rsi_long) & (rsi_thres_long > _rsi_short)
                    & (_vhf_short_ma > vhf_threshold) & (time == 1), 1, 0)
    long = np.where((supertd == -1) | (time == 0), -1, long)
    # Signal - value of 2 to be a sell, value of 0 is neutral not buy NOR sell, and a value of -2 to close position.
    short = np.where((supertd == -1) & (_vhf_short_ma < _vhf_long_ma) & (_rsi_long > _rsi_short) & (_rsi_short > rsi_thres_short)
                     & (_vhf_short_ma > vhf_threshold) & (time == 1), 2, 0)
    short = np.where((supertd == 1) | (time == 0), -2, short)

    return combine_signals(long, short)


def customer_indicator(close, high, low, start_time, end_time, atr_length, factor, rsi_val, vhf_val, rsi_short, rsi_long, vhf_short, vhf_long, rsi_thres_long, rsi_thres_short, short_ma, long_ma, vhf_threshold):
    SUPERTREND = vbt.pandas_ta('SUPERTREND')
    st = SUPERTREND.run(high, low, close, period=atr_length,
                        multiplier=factor).supertd
    VHF = vbt.pandas_ta('VHF')
    EMA = vbt.pandas_ta('EMA')
    rsi = vbt.RSI.run(close, rsi_val).rsi.values
    _vhf = VHF.run(close, period=vhf_val).vhf._values
    _vhf_short_ma = EMA.run(_vhf, vhf_short).ema.values
    _vhf_long_ma = vbt.MA.run(_vhf, vhf_long).ma.values
    short_mvg = vbt.MA.run(close, short_ma).ma.values
    long_mvg = vbt.MA.run(close, long_ma).ma.values

    _rsi_short = EMA.run(rsi, rsi_short).ema.values
    _rsi_long = vbt.MA.run(rsi, rsi_long).ma.values
    supertd = st.values
    start_time = start_time.to_numpy()
    end_time = end_time.to_numpy()
    return produce_signal(supertd, start_time, end_time, _vhf_short_ma, _vhf_long_ma, _rsi_short, _rsi_long, rsi_thres_long, rsi_thres_short, short_mvg, long_mvg, vhf_threshold)


#super_trend with specific trading time parameters
ind = vbt.IndicatorFactory(
    class_name="Combination",
    short_name="comb",
    input_names=["close", "high", "low", 'start_time', "end_time"],
    param_names=["atr_length", "factor", "rsi_val", "vhf_val", "rsi_short", "rsi_long", "vhf_short",
                 "vhf_long", "rsi_thres_long", "rsi_thres_short", "short_ma", "long_ma", "vhf_threshold"],
    output_names=["long", "short"],
).from_apply_func(
    customer_indicator,
    atr_length=10,
    factor=3,
    rsi_val=14,
    vhf_val=56,
    rsi_short=9,
    rsi_long=28,
    vhf_short=50,
    vhf_long=60,
    rsi_thres_long=65,
    rsi_thres_short=35,
    short_ma=50,
    long_ma=100,
    vhf_threshold=.35,
    keep_pd=True,
)

stocks = ['NVDA']
timeframe = '1m'
fullday = True
for stock in stocks:
    high_price, low_price, close_price, start_time, end_time, ticker_price = get_price_data(
        stock, timeframe=timeframe, fullday=fullday)
    args = ["atr_length", "factor", "rsi_val", "vhf_val", "rsi_short", "rsi_long", "vhf_short",
            "vhf_long", "rsi_thres_long", "rsi_thres_short", "short_ma", "long_ma", "vhf_threshold"]

    res = ind.run(
        close=close_price,
        high=high_price,
        low=low_price,
        start_time=start_time,
        end_time=end_time,
        atr_length=10,
        factor=2.5,
        rsi_val=14,
        vhf_val=56,
        rsi_short=20,
        rsi_long=50,
        vhf_short=28,
        vhf_long=60,
        rsi_thres_long=55,
        rsi_thres_short=45,
        short_ma=50,
        long_ma=200,
        vhf_threshold=0.20,
        param_product=True)

    entries = res.long.values == 1
    exits = res.long.values == -1
    short_entries = res.short.values == 2
    short_exits = res.short.values == -2

    # 0.01 = 1%
    pf_kwargs = dict(size=np.inf, freq=timeframe, sl_stop=.004, tp_stop=.0015)
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
    returns = pf.metrics
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
    print(file_name)
    path = f'Results/Retuns_result_{file_name}_fullday_{fullday}.csv'
    if os.path.isfile(path):
        df.to_csv(path, mode='a', header=False)
    else:
        df.to_csv(path, index=True)

    print(stock)
    pf.plot().show()
    print(file_name)
