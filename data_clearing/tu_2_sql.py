# coding=utf-8

import re
import os
import pymysql
import datetime
import pandas as pd
import numpy as np
from dateutil import parser
from sqlalchemy import create_engine


class DataBase:
    """
    把期权信息写入数据库
    """
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

    def re_create_table(self):
        self.cursor.execute('DROP TABLE IF EXISTS option_info')

        sql = """CREATE TABLE option_info
        (
            inst_id char(10),
            underlying char(10),
            strike_price decimal(6, 4),
            call_put char(1),
            multiplier int,
            first_trading_day date,
            last_trading_day date,
            PRIMARY KEY (inst_id)
        ) """
        self.execute = self.cursor.execute(sql)


def read_symbol_from_TU():
    curr_date = str(datetime.date.today())
    # curr_date = '2020-07-21'
    file_path = u'X:/0.13_上交所ETF期权/3_TU'
    # format_date = datetime.datetime.strftime(parser.parse(curr_date), "%Y-%m-%d")
    format_date = datetime.datetime.strftime(parser.parse('2022-09-26'), "%Y-%m-%d")
    #  ========================== 合约名称 ================================
    symbol_file_name = os.path.join(file_path, u"合约" + format_date + ".csv")
    raw_symbol_df = pd.read_csv(symbol_file_name, skiprows=9, encoding="gbk",
                                usecols=[u"合约", u"基础商品代码", u"执行价", u"上市日", u"到期日", u"期权类型", u"合约数量乘数", u"交易所代码", u"产品类型"])

    raw_symbol_df[u'产品类型'] = [re.sub("[=()\"]", "", x) for x in raw_symbol_df[u'产品类型']]
    raw_symbol_df = raw_symbol_df[raw_symbol_df[u'产品类型'] == "个股期权"]
    raw_symbol_df[u'交易所代码'] = [re.sub("[=()\"]", "", x) for x in raw_symbol_df[u'交易所代码']]
    raw_symbol_df = raw_symbol_df[(raw_symbol_df[u'交易所代码'] == "SSE") | (raw_symbol_df[u'交易所代码'] == "SZSE")]

    neat_symbol_df = pd.DataFrame()
    neat_symbol_df['inst_id'] = [re.sub("[=()\"]", "", x) for x in raw_symbol_df[u'合约']]
    neat_symbol_df['underlying'] = [re.sub("[=()\"]", "", x) for x in raw_symbol_df[u'基础商品代码']]
    neat_symbol_df['strike_price'] = np.array(raw_symbol_df[u'执行价'])
    neat_symbol_df['call_put'] = np.where(raw_symbol_df[u'期权类型'] == u'看涨', "C", "P")
    neat_symbol_df['multiplier'] = np.array(raw_symbol_df[u'合约数量乘数'])
    neat_symbol_df['first_trading_day'] = [re.sub("[=()\"]", "", x) for x in raw_symbol_df[u'上市日']]
    neat_symbol_df['first_trading_day'] = pd.to_datetime(neat_symbol_df['first_trading_day'])
    neat_symbol_df['last_trading_day'] = [re.sub("[=()\"]", "", x) for x in raw_symbol_df[u'到期日']]
    neat_symbol_df['last_trading_day'] = pd.to_datetime(neat_symbol_df['last_trading_day'])
    return neat_symbol_df


df_info = read_symbol_from_TU()
d = DataBase('root', 'womenhaoqiang', '10.21.78.53', 3306, 'etf_minute')
d.re_create_table()
df_info.to_sql('option_info', d.engine, if_exists='append', index=False)
