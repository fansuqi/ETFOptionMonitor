import numpy as np
import pandas as pd


class Data:
    root_path = 'Z:/TickData/'

    def __init__(self, product, date, underlying, exchange):
        self.product = product
        self.date = date
        self.underlying = underlying
        self.exchange = exchange

    def read_option_info(self):
        df = pd.read_csv(
            self.root_path + '/%s/%s/Option_Info_%s.%s.csv' % (product, date.strftime('%Y%m%d'), underlying, exchange))
        return df

    def read_tick_data(self, symbol):
        df = pd.read_csv(
            self.root_path + '%s/%s/%s.csv' % (self.product, self.date.strftime('%Y%m%d'), symbol),
            parse_dates=['time'], index_col=['time'])

        if 'volume' not in df.columns:
            df['volume'] = 0
        if 'amount' not in df.columns:
            df['amount'] = 0
        if 'position' not in df.columns:
            df['position'] = 0
        if 'last' not in df.columns:
            df['last'] = np.nan

        df = df[['bid1', 'ask1', 'bsize1', 'asize1', 'last', 'volume', 'amount', 'position']]
        df.rename({'bsize1': 'bidVolume1', 'asize1': 'askVolume1', 'amount': 'turnover', 'position': 'openInterest'},
                  inplace=True, axis=1)

        df_option_auction = df.between_time('9:25:00', '9:26:00').iloc[-1:]
        df_option_auction.index = [date + pd.to_timedelta('9:25:00')]

        df_close_auction = df.between_time('15:00:00', '15:10:00').iloc[-1:]
        df_close_auction.index = [date + pd.to_timedelta('15:00:00')]

        df_morning = df.between_time('9:30:00', '11:30:00').resample('1Min').last().fillna(method='ffill')
        df_afternoon = df.between_time('13:00:00', '14:57:00').resample('1Min').last().fillna(method='ffill')

        df = pd.concat([df_option_auction, df_morning, df_afternoon, df_close_auction])
        df.index.name = 'time'

        symbol = int(symbol.split('.')[0])
        df['instID'] = symbol

        df['mid'] = (df['bid1'] + df['ask1']) / 2
        return df


product = '300'
date = pd.to_datetime('2021-03-31')
underlying = '510300'
exchange = 'SH'

r = 0.03
d = Data(product, date, underlying, exchange)
df_info = d.read_option_info()
for last_trading_day, df_info_by_last_trading_day in df_info.groupby('last_trading_day'):
    data = {}
    for strike, df_info_by_strike in df_info_by_last_trading_day.groupby('strike_price'):
        call_symbol = df_info_by_strike[df_info_by_strike['call_put'] == 'C']['option_code'].iloc[0]
        put_symbol = df_info_by_strike[df_info_by_strike['call_put'] == 'P']['option_code'].iloc[0]
        df = pd.merge_asof(d.read_tick_data(call_symbol), d.read_tick_data(put_symbol),
                           left_index=True, right_index=True, suffixes=('_call', '_put'))
        data[strike] = df

    df_all_option = pd.concat(data, names=('strike', 'time'))

    # check auction
    df_all_option.loc[df_all_option['bid1_call'] == df_all_option['ask1_call'], ['bid1_call', 'ask1_call']] = np.nan
    df_all_option.loc[df_all_option['bid1_put'] == df_all_option['ask1_put'], ['bid1_put', 'ask1_put']] = np.nan

    maturity = (pd.to_datetime(last_trading_day) + pd.to_timedelta('15:30:00') - df_all_option.index.get_level_values('time')) / pd.to_timedelta('365D')

    # calculate synthetic spot
    strike_discount = df_all_option.index.get_level_values('strike') * np.exp(-r * maturity)
    syn_bid = df_all_option['bid1_call'] + strike_discount - df_all_option['ask1_put']
    syn_ask = df_all_option['ask1_call'] + strike_discount - df_all_option['bid1_put']

    df = pd.DataFrame({'synthetic': (syn_bid.groupby(level=1).max() +
                                     syn_ask.groupby(level=1).min()) / 2,
                       'volume_call': df_all_option['volume_call'].groupby(level=1).sum(),
                       'volume_put': df_all_option['volume_put'].groupby(level=1).sum()})
