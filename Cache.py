import time
import numpy as np
import pandas as pd
from ctypes import *
import os


class Cache:
    def __init__(self, option, trading_day):
        self._init_dll()
        self._init_subscribe(option)
        self.trading_Day = trading_day

        self.columns = ["inst_id", "time", "bid1", "ask1", "bidVolume1", "askVolume1",
                        "last", "volume", "turnOver", "openInterest"]

    def _init_dll(self):
        # 加载期货行情DLL
        self.etf_dll = cdll.LoadLibrary('./md_sopt.dll')
        self.etf_dll.init.restype = c_bool
        self.etf_dll.sub.restype = c_bool
        self.etf_dll.get_md.restype = c_char_p

        # 登录行情服务器
        # front = bytes('tcp://116.246.40.193:61623', 'utf-8')
        front = bytes('tcp://101.230.102.100:61623', 'utf-8')
        broker_id = bytes('2000', 'utf-8')

        # front = bytes("tcp://180.168.146.187:10131", "utf-8")
        # broker_id = bytes("9999", "utf-8")

        res = self.etf_dll.init(front, broker_id)
        if not res:
            raise Exception('Futures CTP Connection Is Error')
        print('CTP Futures Connection Successful!')

    def _init_subscribe(self, option):
        columns = ['bid1', 'ask1', 'bidVolume1', 'askVolume1', 'last']
        # time_cache = None
        # dct = {}
        lst_symbol = ['510050', '510300', '159919', '510500', '159915', '159922']  # TODO: NOT ROBUST
        lst_symbol += option.df.index.to_list()
        # self.df_cache = pd.DataFrame(index=lst_underlying, columns=columns)

        # 订阅行情
        for symbol in lst_symbol:
            self._subscribe(symbol)
            # dct[underlying] = OptionChain(underlying)
            # for option_symbol in dct[underlying].df.index:
            #     subscribe(option_symbol)

    def _subscribe(self, symbol):
        result = self.etf_dll.sub(bytes(str(symbol), "utf-8"))
        if not result:
            raise Exception("subscription is error")

    def get_market_data(self, symbol):
        md = self.etf_dll.get_md(bytes(str(symbol), "utf-8"))
        md = bytes.decode(md)
        # print(dict(zip(self.columns, md)))

        # for i in range(10):
        #     md = self.futures_dll.get_md()
        #     md = bytes.decode(md)
        #     if not md:  # md为空的情况
        #         time.sleep(0.1)
        #         continue
        #
        #     md = md.split(",")
        # if len(md) != 10:  # md出现某些字段为空的情况
        #     print(len(md))
        #     return False
            # time_cache = md[1]
        if len(md) <= 5:
            return False
        md = md.split(",")
        md[1] = pd.to_timedelta(md[1]) + self.trading_Day
        result = dict(zip(self.columns, md))
        result['bid1'] = float(result['bid1'])
        result['ask1'] = float(result['ask1'])
        result['last'] = float(result['last'])
        result['askVolume1'] = int(result['askVolume1'])
        result['bidVolume1'] = int(result['bidVolume1'])
        result['mid'] = (result['bid1'] + result['ask1']) / 2
        return result

