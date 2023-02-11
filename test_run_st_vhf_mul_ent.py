import vectorbt as vbt
import pandas as pd
import numpy as np
import os
from get_price import get_specific_timedata
from indicators import range_filter
import datetime

today = datetime.datetime.now().date()
date_format = today.strftime("%m/%d/%Y")


def produce_signal(supertd, entry_price, low, high, start_time, end_time, _vhf_short_ma, _vhf_long_ma, _ma_short, _ma_long, vhf_threshold):
    # Signal - value of 1 to be a buy, value of 0 is neutral not sell NOR buy, and a value of -1 to close position.
    time = np.where((start_time == True) & (end_time == True), 1, 0)
    long = np.where((supertd == 1) & (_vhf_short_ma > _vhf_long_ma) & (_ma_short > _ma_long) & (entry_price > low)
                    & (_vhf_short_ma > vhf_threshold) & (time == 1), 1, 0)
    long = np.where((time == 0) | (supertd == -1), -1, long)
    # Signal - value of 2 to be a sell, value of 0 is neutral not buy NOR sell, and a value of -2 to close position.
    short = np.where((supertd == -1) & (_vhf_short_ma > _vhf_long_ma) & (_ma_short < _ma_long) & (entry_price < high)
                     & (_vhf_short_ma > vhf_threshold) & (time == 1), 2, 0)
    short = np.where((time == 0) | (supertd == 1), -2, short)

    return long, short


def customer_indicator(close, high, low, entry, start_time, end_time, atr_length, factor, vhf_val, ma_short, ma_long, vhf_short, vhf_long, vhf_threshold):
    SUPERTREND = vbt.pandas_ta('SUPERTREND')
    st = SUPERTREND.run(high, low, close, period=atr_length,
                        multiplier=factor).supertd
    VHF = vbt.pandas_ta('VHF')
    EMA = vbt.pandas_ta('EMA')
    _vhf = VHF.run(close, period=vhf_val).vhf.values
    _vhf_short_ma = vbt.MA.run(_vhf, vhf_short).ma.values
    _vhf_long_ma = vbt.MA.run(_vhf, vhf_long).ma.values

    _ma_short = EMA.run(close, ma_short).ema.values
    _ma_long = EMA.run(close, ma_long).ema.values
    supertd = st.values
    start_time = start_time.to_numpy()
    end_time = end_time.to_numpy()
    low = low.to_numpy()
    high = high.to_numpy()
    entry_price = entry.to_numpy()
    return produce_signal(supertd,entry_price, low, high, start_time, end_time, _vhf_short_ma, _vhf_long_ma, _ma_short, _ma_long, vhf_threshold)


# super_trend, multiplier, chop, vhf_val, ma_long, ma_short, stock_ma, stocksma, chop_ma, chopsma, vhf_ma, vhfsma
ind = vbt.IndicatorFactory(
    class_name="Combination",
    short_name="comb",
    input_names=["close", "high", "low", 'entry', 'start_time', "end_time"],
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
    vhf_threshold=.2,
    keep_pd=True,
)

stocks = ['SQQQ']
timeframe = '1m'
end = datetime.datetime.now().date()
start = end - datetime.timedelta(days=7)


for stock in stocks:
    high_price, low_price, close_price, start_time, end_time, ticker_price = get_specific_timedata(
        stock, start_time=start.strftime("%m/%d/%Y"), end_time=end.strftime("%m/%d/%Y"))

    lowercase_columns = [col.lower().strip() for col in ticker_price.columns]
    ticker_price.columns = lowercase_columns
    entry_price = range_filter(ticker_price, range_qty=2.3)['rf']

    args = ["atr_length", "factor", "vhf_val", "ma_short", "ma_long", "vhf_short",
            "vhf_long", "vhf_threshold"]

    res = ind.run(
        close=close_price,
        high=high_price,
        low=low_price,
        entry = entry_price,
        start_time=start_time,
        end_time=end_time,
        atr_length=[25],
        factor=[2.5],
        vhf_val=[56],
        ma_short=[50],
        ma_long=[200],
        vhf_short=[21],
        vhf_long=[28],
        vhf_threshold=[.2],
        param_product=True)

    entries = res.long.values == 1
    exits = res.long.values == -1
    short_entries = res.short.values == 2
    short_exits = res.short.values == -2

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

    path = f'Results/Retuns_result_{file_name}_test.csv'
    if os.path.isfile(path):
        df.to_csv(path, mode='a', header=False)
    else:
        df.to_csv(path, index=True)

    print(stock)
    pf.plot().show()
    print(file_name)
