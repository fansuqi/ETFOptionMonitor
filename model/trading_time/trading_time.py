import pandas as pd
from model.trading_time.chinese_trading_day import today


# open_auction = pd.Series(pd.to_timedelta('9:25:00'))

__morning = pd.Series(pd.timedelta_range('9:30:00', '11:29:00', freq='1Min'))
__afternoon = pd.Series(pd.timedelta_range('13:00:00', '14:56:00', freq='1Min'))
__close_auction = pd.Series(pd.to_timedelta('15:00:00'))

idx_trading_time = (today + pd.concat([__morning, __afternoon, __close_auction])).to_numpy()
