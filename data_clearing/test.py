import pandas as pd
from model.database import db
from model.trading_time import trading_day_offset, today

lst = []
for offset in range(8):
    df_call = db.get_minute_data_by_symbol(trading_day_offset(today, offset), '90000613')
    df_put = db.get_minute_data_by_symbol(trading_day_offset(today, offset), '90000622')
    syn1 = df_call['mid'] + 5.0 - df_put['mid']

    df_call = db.get_minute_data_by_symbol(trading_day_offset(today, offset), '90000585')
    df_put = db.get_minute_data_by_symbol(trading_day_offset(today, offset), '90000594')
    syn2 = df_call['mid'] + 5.0 - df_put['mid']

    lst.insert(0, (syn1 - syn2) * 10000)

print(pd.concat(lst))
pd.concat(lst).to_csv('D:/syn.csv')

