import numpy as np
import pandas as pd
from model.trading_time.chinese_trading_day import today, open_time, break_start_time, break_end_time, close_time, trading_day_count


def cal_maturity(last_trading_day, time, method=0):
    if method == 0:
        return __cal_maturity_trading_day(last_trading_day, time)
    elif method == 1:
        return __cal_maturity_calendar_day(last_trading_day, time)
    else:
        raise Exception


def __cal_maturity_calendar_day(last_trading_day, time):
    maturity = (last_trading_day + pd.to_timedelta('15:30:00') - time).total_seconds() / (365 * 24 * 3600)
    return maturity


def __cal_maturity_trading_day(last_trading_day, date_time):
    date = date_time.strftime('%Y-%m-%d')
    time = date_time - pd.to_datetime(date)
    time_decay_today = np.where(time < break_start_time,
                                np.where(time < open_time, pd.to_timedelta('4H'), break_start_time - time + pd.to_timedelta('2H')),
                                np.where(time < break_end_time,
                                         pd.to_timedelta('2H'),
                                         np.where(time > close_time, pd.to_timedelta('30min'), close_time - time)))

    time_decay_today = pd.to_timedelta(time_decay_today) / pd.to_timedelta('4H')
    if type(date) == str:
        return (time_decay_today + trading_day_count(date, last_trading_day.strftime('%Y-%m-%d'))) / 244
    return (time_decay_today + trading_day_count(date.to_list(), last_trading_day.strftime('%Y-%m-%d'))) / 244


if __name__ == '__main__':
    a = pd.to_datetime('2021-04-20 9:25:00')
    print(__cal_maturity_calendar_day('2021-04-28', pd.to_datetime('2021-04-20 13:35:00')))
