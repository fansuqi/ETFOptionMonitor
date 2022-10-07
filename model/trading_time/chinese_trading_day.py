import numpy as np
import pandas as pd


_holidays = ['2017-01-02',
             '2017-01-27', '2017-01-30', '2017-01-31', '2017-02-01', '2017-02-02',
             '2017-04-03', '2017-04-04',
             '2017-05-01',
             '2017-05-29', '2017-05-30',
             '2017-10-02', '2017-10-03', '2017-10-04', '2017-10-05', '2017-10-06',
             '2018-01-01',
             '2018-02-15', '2018-02-16', '2018-02-19', '2018-02-20', '2018-02-21',
             '2018-04-05', '2018-04-06',
             '2018-04-30', '2018-05-01',
             '2018-06-18',
             '2018-09-24',
             '2018-10-01', '2018-10-02', '2018-10-03', '2018-10-04', '2018-10-05',
             '2018-12-31',
             '2019-01-01',
             '2019-02-04', '2019-02-05', '2019-02-06', '2019-02-07', '2019-02-08',
             '2019-04-05',
             '2019-05-01', '2019-05-02', '2019-05-03',
             '2019-06-07',
             '2019-09-13',
             '2019-10-01', '2019-10-02', '2019-10-03', '2019-10-04', '2019-10-07',
             '2020-01-01',
             '2020-01-24', '2020-01-27', '2020-01-28', '2020-01-29', '2020-01-30', '2020-01-31',
             '2020-04-06',
             '2020-05-01', '2020-05-04', '2020-05-05',
             '2020-06-25', '2020-06-26',
             '2020-10-01', '2020-10-02', '2020-10-05', '2020-10-06', '2020-10-07', '2020-10-08',
             '2021-01-01',
             '2021-02-11', '2021-02-12', '2021-02-15', '2021-02-16', '2021-02-17',
             '2021-04-05', '2021-05-03', '2021-05-04', '2021-05-05', '2021-06-14',
             '2021-09-20', '2021-09-21', '2021-10-01', '2021-10-04', '2021-10-05', '2021-10-06', '2021-10-07',
             '2022-01-03',
             '2022-01-31', '2022-02-01', '2022-02-02', '2022-02-03', '2022-02-04',
             '2022-04-04', '2022-04-05',
             '2022-05-02', '2022-05-03', '2022-05-04',
             '2022-06-03',
             '2022-09-12',
             '2022-10-03', '2022-10-04', '2022-10-05', '2022-10-06', '2022-10-07']


cn_holiday_calendar = np.busdaycalendar(weekmask='1111100', holidays=_holidays)
cn_cbd = pd.offsets.CustomBusinessDay(holidays=_holidays, weekmask='1111100')


def trading_day_offset(date, offset):
    return pd.to_datetime(date) - cn_cbd * offset


def trading_day_range(startDate, endDate):
    return pd.date_range(startDate, endDate, freq=cn_cbd)


def trading_day_count(begin_date, end_date):
    return np.busday_count(begin_date, end_date, holidays=_holidays)


date = pd.Timestamp.today().replace(hour=0, minute=0, second=0, microsecond=0)
today = pd.Timestamp.today().replace(hour=0, minute=0, second=0, microsecond=0)
open_time = pd.to_timedelta('9:30:00')
break_start_time = pd.to_timedelta('11:30:00')
break_end_time = pd.to_timedelta('13:00:00')
close_time = pd.to_timedelta('15:00:00')


if __name__ == '__main__':
    yesterday = trading_day_offset(pd.datetime.today(), -1)
    print(yesterday)
    
    t = pd.to_datetime('2019-06-06')
    # a = np.load('chinese_holiday.npy')
    print(t + cn_cbd)

    print(np.busday_count(pd.to_datetime('2020-04-30').date(), pd.to_datetime('2020-05-10').date(), holidays=_holidays))
