import numpy as np
import pandas as pd
from model.database import db


class OptionInfo:
    def __init__(self, db):
        self.df = db.get_option_info()

    def get_next_strike(self, underlying, month, strike, nxt):
        """
        :param month: 0, 1, 2 or 3
        :param strike: strike
        :param nxt: 1 or -1
        :return:
        """
        last_trading_day = self.get_last_trading_day_array(underlying)[month]

        arr_strike_price = self.get_strike_price_arr(underlying, last_trading_day)
        idx = np.where(arr_strike_price == strike)[0][0] + nxt
        if idx >= len(arr_strike_price):
            idx = 0
        elif idx < 0:
            idx = len(arr_strike_price) - 1
        strike = arr_strike_price[idx]

        # parity = (self.df['underlying'] == underlying) & (self.df['last_trading_day'] == last_trading_day) & (self.df['strike_price'] == strike)
        # call_symbol = self.df[(self.df['call_put'] == 'C') & parity].index[0]
        # put_symbol = self.df[(self.df['call_put'] == 'P') & parity].index[0]
        call_symbol, put_symbol = self.get_parity(underlying, strike, last_trading_day)
        return month, strike, pd.to_datetime(last_trading_day), call_symbol, put_symbol

    def get_next_month(self, underlying, month, strike, nxt):
        arr_last_trading_day = self.get_last_trading_day_array(underlying)
        month += nxt
        if month >= len(arr_last_trading_day):
            month = 0
        elif month < 0:
            month = len(arr_last_trading_day) - 1
        last_trading_day = arr_last_trading_day[month]

        strike_price = self.get_strike_price_arr(underlying, last_trading_day)
        if strike > strike_price[-1]:
            strike = strike_price[-1]
        elif strike < strike_price[0]:
            strike = strike_price[0]

        # parity = (self.df['underlying'] == underlying) & (self.df['last_trading_day'] == last_trading_day) & (self.df['strike_price'] == strike)
        # call_symbol = self.df[(self.df['call_put'] == 'C') & parity].index[0]
        # put_symbol = self.df[(self.df['call_put'] == 'P') & parity].index[0]
        call_symbol, put_symbol = self.get_parity(underlying, strike, last_trading_day)
        return month, strike, pd.to_datetime(last_trading_day), call_symbol, put_symbol

    def get_option_chain(self):
        return self.df['option_code'].tolist()

    def get_option_symbol(self, underlying, last_trading_day, strike, option_type):
        ret = self.df[(self.df['underlying'] == underlying) &
                      (self.df['last_trading_day'] == pd.to_datetime(last_trading_day)) &
                      (self.df['strike_price'] == float(strike)) &
                      (self.df['call_put'] == option_type)]
        return ret.index[0]

    def get_last_trading_day_array(self, underlying):
        arr_lat_trading_day = self.df[self.df['underlying'] == underlying]['last_trading_day'].unique()
        arr_lat_trading_day.sort()
        return arr_lat_trading_day

    def get_last_trading_day(self, underlying, month):
        arr_last_trading_day = self.get_last_trading_day_array(underlying)
        return pd.to_datetime(arr_last_trading_day[month])

    def get_strike_price_arr(self, underlying, last_trading_day, dividend=True):
        arr_strike_price = self.df[(self.df['underlying'] == underlying) &
                                   (self.df['last_trading_day'] == pd.to_datetime(last_trading_day)) &
                                   (self.df['call_put'] == 'C') &
                                   (self.df['multiplier'] == 10000)]['strike_price'].to_numpy()
        arr_strike_price.sort()
        return arr_strike_price

    def get_option_info(self, symbol):
        return self.df.loc[symbol]

    def get_parity(self, underlying, strike, last_trading_day):
        parity = (self.df['underlying'] == underlying) & (self.df['last_trading_day'] == last_trading_day) & (self.df['strike_price'] == strike)
        call_symbol = self.df[(self.df['call_put'] == 'C') & parity].index[0]
        put_symbol = self.df[(self.df['call_put'] == 'P') & parity].index[0]
        return call_symbol, put_symbol


option_info = OptionInfo(db)
