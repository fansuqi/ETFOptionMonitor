import numpy as np
import pandas as pd
import pymysql
from sqlalchemy import create_engine


class DataBase:
    def __init__(self, root, password, host, port, database):
        self.root = root
        self.password = password
        self.host = host
        self.port = port
        self.database = database

        self.__init_engine()
        self.__init_conn()

    def __init_engine(self):
        self.engine = create_engine('mysql+pymysql://%s:%s@%s:%s/%s' %
                                    (self.root, self.password, self.host, self.port, self.database))

    def __init_conn(self):
        conn = pymysql.connect(host=self.host, port=self.port,
                               user=self.root, password=self.password, db=self.database)
        self.cursor = conn.cursor()

    def re_create_table(self, table_name):
        self.cursor.execute('DROP TABLE IF EXISTS %s' % table_name)

        sql = """CREATE TABLE %s
        (
            instID int,
            `time` datetime,
            bid1 decimal(6, 4),
            ask1 decimal(6, 4),
            `last` decimal(6, 4),
            bidVolume1 int,
            askVolume1 int,
            volume int,
            turnover bigint,
            openInterest int,
            PRIMARY KEY (instID, `time`)
        ) """ % table_name
        self.cursor.execute(sql)


if __name__ == '__main__':
    from model.trading_time import trading_day_range
    # date = pd.to_datetime('2021-01-22')
    # '2021-05-13'
    for date in trading_day_range('2021-06-05', '2021-06-15'):
        print(date)
        d = DataBase('root', 'womenhaoqiang', '10.21.78.53', 3306, 'etf_minute')
        table_name = 'minute_data_%s' % date.strftime('%Y%m%d')
        d.re_create_table(table_name)

        for product, underlying, exchange in [['50', '510050', 'SH'], ['300', '510300', 'SH'], ['300', '159919', 'SZ']]:
            df = pd.read_csv('Z:/TickData/%s/%s/%s.%s.csv' % (product, date.strftime('%Y%m%d'), underlying, exchange),
                             parse_dates=['time'], index_col=['time'],
                             usecols=['time', 'bid1', 'ask1', 'bsize1', 'asize1', 'last', 'volume', 'amount'])
            df.rename({'bsize1': 'bidVolume1', 'asize1': 'askVolume1', 'amount': 'turnover'},
                      inplace=True, axis=1)

            df_option_auction = df.between_time('9:25:00', '9:26:00').iloc[-1:]
            df_option_auction.index = [date + pd.to_timedelta('9:25:00')]

            df_morning = df.between_time('9:30:00', '11:30:00').resample('1Min').last().fillna(method='ffill')
            df_afternoon = df.between_time('13:00:00', '15:00:00').resample('1Min').last().fillna(method='ffill')

            df_close_auction = df.between_time('15:00:00', '15:10:00').iloc[-1:]
            if df_close_auction.empty:
                df_close_auction = pd.DataFrame(index=[date + pd.to_timedelta('15:00:00')])

            df_close_auction.index = [date + pd.to_timedelta('15:00:00')]

            df = pd.concat([df_option_auction, df_morning, df_afternoon, df_close_auction])
            df.index.name = 'time'
            df['instID'] = int(underlying)

            df.to_sql('minute_data_%s' % date.strftime('%Y%m%d'), d.engine, if_exists='append')

            df_info = pd.read_csv('Z:/TickData/%s/%s/Option_Info_%s.%s.csv' % (product, date.strftime('%Y%m%d'), underlying, exchange))
            for symbol in df_info['option_code']:
                df = pd.read_csv('Z:/TickData/%s/%s/%s.csv' % (product, date.strftime('%Y%m%d'), symbol),
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
                df['instID'] = int(symbol.split('.')[0])

                print(symbol)
                df.to_sql('minute_data_%s' % date.strftime('%Y%m%d'), d.engine, if_exists='append')
