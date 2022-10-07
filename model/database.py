import pandas as pd
from sqlalchemy import create_engine


class DataBase:
    def __init__(self, root, password, host, port, database):
        self.root = root
        self.password = password
        self.host = host
        self.port = port
        self.database = database

        self.__init_engine()

    def __init_engine(self):
        self.engine = create_engine('mysql+pymysql://%s:%s@%s:%s/%s' %
                                    (self.root, self.password, self.host, self.port, self.database))

    # def get_settle_data(self, date):
    #     sql = """
    #     SELECT strike, underlying, `month`, last_trading_day, bid1_call, ask1_call, bid1_put, ask1_put, bid1, ask1 FROM
    #     (SELECT strike, underlying, `month`, last_trading_day, bid1_call, ask1_call, bid1_put, ask1_put FROM option_data_%s WHERE `time` = '%s 15:00:00') AS o
    #     LEFT JOIN (SELECT bid1, ask1, symbol FROM underlying_data_%s WHERE `time` = '%s 15:00:00') AS u
    #     ON o.underlying = u.symbol;
    #     """ % (date.strftime('%Y%m%d'), date.strftime('%Y-%m-%d'), date.strftime('%Y%m%d'), date.strftime('%Y-%m-%d'))
    #     df = pd.read_sql(sql, self.engine, index_col=['strike', 'underlying', 'month'], parse_dates=['last_trading_day'])
    #     df['mid_call'] = (df['bid1_call'] + df['ask1_call']) / 2
    #     df['mid_put'] = (df['bid1_put'] + df['ask1_put']) / 2
    #     df['mid'] = (df['bid1'] + df['ask1']) / 2
    #     return df

    def get_settle_data(self, date):
        sql = """
        SELECT instID, bid1, ask1 FROM minute_data_%s WHERE `time` = '%s 14:55:00'
        """ % (date.strftime('%Y%m%d'), date.strftime('%Y-%m-%d'))
        df = pd.read_sql(sql, self.engine, index_col=['instID'])
        df['mid'] = (df['bid1'] + df['ask1']) / 2
        df.index = df.index.astype(str)  # TODO: 这里很有问题
        return df

    def get_minute_data_by_symbol(self, date, symbol):
        sql = """SELECT `time`, bid1, ask1 FROM minute_data_%s AS m WHERE instID = '%s';""" % (date.strftime('%Y%m%d'), symbol)
        df = pd.read_sql(sql, self.engine, parse_dates=['time'], index_col=['time'])
        df['mid'] = (df['bid1'] + df['ask1']) / 2
        return df

    def get_option_minute_data(self, date, underlying, call_put, strike, last_trading_day):
        sql = "SELECT `time`, bid1, ask1, volume " +\
              "FROM (SELECT instID, `time`, bid1, ask1, volume FROM minute_data_%s) AS m " % date.strftime('%Y%m%d') + \
              "LEFT JOIN (SELECT inst_id, call_put, strike_price, last_trading_day, underlying FROM option_info) AS o " +\
              "ON m.instID = o.inst_id " +\
              "WHERE underlying = %s AND call_put = '%s' AND strike_price = %s AND last_trading_day='%s';" % (underlying, call_put, strike, last_trading_day.strftime('%Y%m%d'))

        df = pd.read_sql(sql, self.engine, parse_dates=['time'], index_col=['time'])
        df['mid'] = (df['bid1'] + df['ask1']) / 2
        return df

    def get_underlying_minute_data(self, date, underlying):
        sql = "SELECT `time`, bid1, ask1 " + \
              "FROM (SELECT instID, `time`, bid1, ask1 FROM minute_data_%s) AS m " % date.strftime('%Y%m%d') + \
              "WHERE instID = '%s';" % underlying
        df = pd.read_sql(sql, self.engine, parse_dates=['time'], index_col=['time'])
        df['mid'] = (df['bid1'] + df['ask1']) / 2
        return df

    def get_minute_data_parity(self, date, underlying, strike, last_trading_day):
        df_call = self.get_option_minute_data(date, underlying, 'C', strike, last_trading_day)
        df_put = self.get_option_minute_data(date, underlying, 'P', strike, last_trading_day)
        df_underlying = self.get_underlying_minute_data(date, underlying)
        return df_call, df_put, df_underlying

    def get_multi_minute_data_parity(self, arr_date, strike, last_trading_day, underlying):
        call, put, list_underlying = [], [], []
        for date in arr_date:
            df_call, df_put, df_underlying = self.get_minute_data_parity(date, strike, last_trading_day, underlying)
            call.append(df_call)
            put.append(df_put)
            list_underlying.append(df_underlying)
        return pd.concat(call), pd.concat(put), pd.concat(list_underlying)

    def get_option_info(self):
        sql = "SELECT inst_id, underlying, strike_price, call_put, last_trading_day, multiplier FROM etf_minute.option_info"
        df = pd.read_sql(sql, self.engine, parse_dates=['last_trading_day'], index_col=['inst_id'])
        return df

    def get_curve(self, underlying, last_trading_day, time):
        sql = """
        SELECT instID, bid1, ask1, strike_price, call_put
        FROM minute_data_%s AS m
        LEFT JOIN option_info AS o
        ON m.instID = o.inst_id
        WHERE last_trading_day = '%s' AND underlying = %s AND `time` = '%s'
        """ % (time.strftime('%Y%m%d'), last_trading_day.strftime('%Y%m%d'), underlying, time.strftime('%Y-%m-%d %H:%M:%S'))
        df = pd.read_sql(sql,  self.engine)
        return df


dialect = 'root'
driver = 'pymysql'
username = 'root'
password = 'womenhaoqiang'
host = '10.21.78.53'
port = 3306
database = 'etf_minute'

db = DataBase(username, password, host, port, database)
