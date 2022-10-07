import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template

from Cache import Cache
from model.check_data import check_data
from model.pricing import cal_implied_vol, cal_maturity
from model.trading_time import today, trading_day_offset
from model.database import db
from model.option_info import option_info
from model.trading_time.trading_time import idx_trading_time

from view import bp_option_info

app = Flask(__name__)
app.register_blueprint(bp_option_info)

r = 0.03
q = 0


try:
    c = Cache(option_info, today)
    # print()
except Exception as e:
    print("CTP CONNECTION FAILED.")

syn_dct = {'159919': {pd.to_datetime('2022-12-28'): 4.1,
                      pd.to_datetime('2023-03-22'): 4.1,
                      pd.to_datetime('2022-09-28'): 4.1,
                      pd.to_datetime('2022-10-26'): 4.1},
           '159915': {pd.to_datetime('2022-12-28'): 2.25,
                      pd.to_datetime('2023-03-22'): 2.25,
                      pd.to_datetime('2022-11-23'): 2.25,
                      pd.to_datetime('2022-10-26'): 2.25},
           '159922': {pd.to_datetime('2022-12-28'): 6.0,
                      pd.to_datetime('2023-03-22'): 6.0,
                      pd.to_datetime('2022-11-23'): 6.0,
                      pd.to_datetime('2022-10-26'): 6.0},
           '510500': {pd.to_datetime('2022-12-28'): 6.0,
                      pd.to_datetime('2023-03-22'): 6.0,
                      pd.to_datetime('2022-11-23'): 6.0,
                      pd.to_datetime('2022-10-26'): 6.0},
           '510050': {pd.to_datetime('2022-12-28'): 2.7,
                      pd.to_datetime('2023-03-22'): 2.7,
                      pd.to_datetime('2022-09-28'): 2.7,
                      pd.to_datetime('2022-10-26'): 2.7},
           '510300': {pd.to_datetime('2022-12-28'): 4.0,
                      pd.to_datetime('2023-03-22'): 4.0,
                      pd.to_datetime('2022-09-28'): 4.0,
                      pd.to_datetime('2022-10-26'): 4.0}}

underlying_dct = {'159919': 0.0, '510300': 0.0, '510050': 0.0, '510500': 0.0, '159915': 0.0, '159922': 0.0}


@app.route('/iv/<underlying>')
def iv(underlying):
    month = 0
    last_trading_day = option_info.get_last_trading_day(underlying, month)
    strike = syn_dct[underlying][last_trading_day]

    call_symbol = option_info.get_option_symbol(underlying, last_trading_day, strike, 'C')
    put_symbol = option_info.get_option_symbol(underlying, last_trading_day, strike, 'P')

    return render_template('ImpliedVol.html', underlying=underlying, strike=strike,
                           month=month, lastTradingDay=pd.to_datetime(last_trading_day).strftime('%m-%d'),
                           callSymbol=call_symbol, putSymbol=put_symbol)


@app.route('/skew')
def skew():
    underlying = request.args.get('underlying')
    last_trading_day = request.args.get('lastTradingDay')
    buy_strike = request.args.get('buyStrike')
    buy_type = request.args.get('buyType')
    sell_strike = request.args.get('sellStrike')
    sell_type = request.args.get('sellType')

    if len(request.args) == 0:
        return render_template('SkewTrading.html')

    buy_symbol = option_info.get_option_symbol(underlying, last_trading_day, buy_strike, 'C' if buy_type == 'CALL' else 'P')
    sell_symbol = option_info.get_option_symbol(underlying, last_trading_day, sell_strike, 'C' if sell_type == 'CALL' else 'P')
    return render_template('SkewTrading.html', underlying=underlying, lastTradingDay=last_trading_day,
                           buyStrike=buy_strike, buyType=buy_type, buySymbol=buy_symbol,
                           sellStrike=sell_strike, sellType=sell_type, sellSymbol=sell_symbol)


@app.route('/data/ts/skew')
def _skew():
    offset = int(request.args.get('offset'))
    buy_symbol, sell_symbol = request.args.get('buySymbol'), request.args.get('sellSymbol')
    buy_symbol_option_info = option_info.get_option_info(buy_symbol)
    sell_symbol_option_info = option_info.get_option_info(sell_symbol)

    syn_strike = syn_dct[buy_symbol_option_info['underlying']][buy_symbol_option_info['last_trading_day']]
    syn_symbol = option_info.get_parity(buy_symbol_option_info['underlying'], syn_strike,
                                        buy_symbol_option_info['last_trading_day'])
    df_call = db.get_minute_data_by_symbol(trading_day_offset(today, offset), syn_symbol[0]).between_time('9:30:00', '15:00:00')
    df_put = db.get_minute_data_by_symbol(trading_day_offset(today, offset), syn_symbol[1]).between_time('9:30:00', '15:00:00')

    df_call['mid'].loc[(df_call['bid1'] == df_call['ask1']) | (df_call['bid1'] <= 0) | (df_call['ask1'] <= 0)] = np.nan
    df_put['mid'].loc[(df_put['bid1'] == df_put['ask1']) | (df_put['bid1'] <= 0) | (df_put['ask1'] <= 0)] = np.nan

    maturity = cal_maturity(buy_symbol_option_info['last_trading_day'], df_call.index)
    synthetic_underlying = df_call['mid'] + syn_strike * np.exp(-r * maturity) - df_put['mid']

    buy_strike = buy_symbol_option_info['strike_price']
    buy_type = buy_symbol_option_info['call_put']
    df_buy = db.get_minute_data_by_symbol(trading_day_offset(today, offset), buy_symbol)
    df_buy = df_buy.between_time('9:30:00', '15:00:00')
    df_buy['iv'] = cal_implied_vol(df_buy['mid'], synthetic_underlying, float(buy_strike), maturity, r, q, True if buy_type == 'C' else False)[0]
    df_buy['iv'] = np.where(df_buy['iv'] == 0, np.nan, df_buy['iv'])

    sell_strike = sell_symbol_option_info['strike_price']
    sell_type = sell_symbol_option_info['call_put']
    df_sell = db.get_minute_data_by_symbol(trading_day_offset(today, offset), sell_symbol)
    df_sell = df_sell.between_time('9:30:00', '15:00:00')
    df_sell['iv'] = cal_implied_vol(df_sell['mid'], synthetic_underlying, float(sell_strike), maturity, r, q, True if sell_type == 'C' else False)[0]
    df_sell['iv'] = np.where(df_sell['iv'] == 0, np.nan, df_sell['iv'])
    df = pd.DataFrame({'vol_diff': df_buy['iv'] - df_sell['iv'],
                       'synthetic': np.round(synthetic_underlying, 4)})

    df['vol_diff'] = np.where(check_data(df_buy['bid1'], df_buy['ask1']) | check_data(df_sell['bid1'], df_sell['ask1']) | check_data(df_call['bid1'], df_call['ask1']) | check_data(df_put['bid1'], df_put['ask1']),
                              np.nan, df['vol_diff'])

    if offset == 0:
        df = pd.DataFrame(df, index=idx_trading_time)
    df = df.between_time('9:30:00', '14:56:00')
    return df.to_json(orient='split')


@app.route('/data/snapshot/skew')
def _snap_shot_skew():
    buy_symbol, sell_symbol = request.args.get('buySymbol'), request.args.get('sellSymbol')

    buy_option_data = c.get_market_data(buy_symbol)
    if not buy_option_data:
        return jsonify({'status': False})

    sell_option_data = c.get_market_data(sell_symbol)
    if not sell_option_data:
        return jsonify({'status': False})

    buy_symbol_option_info = option_info.get_option_info(buy_symbol)
    sell_symbol_option_info = option_info.get_option_info(sell_symbol)
    time = buy_option_data['time']
    maturity = cal_maturity(buy_symbol_option_info['last_trading_day'], time)

    syn_strike = syn_dct[buy_symbol_option_info['underlying']][buy_symbol_option_info['last_trading_day']]
    syn_symbol = option_info.get_parity(buy_symbol_option_info['underlying'], syn_strike,
                                        buy_symbol_option_info['last_trading_day'])
    syn_buy_data = c.get_market_data(syn_symbol[0])
    syn_sell_data = c.get_market_data(syn_symbol[1])
    if not syn_buy_data:
        return jsonify({'status': False})
    if not syn_sell_data:
        return jsonify({'status': False})
    synthetic_underlying = syn_buy_data['mid'] + syn_strike * np.exp(-r * maturity) - syn_sell_data['mid']

    buy_iv, buy_delta, buy_gamma, buy_vega, buy_theta = \
        cal_implied_vol(np.array([buy_option_data['mid'], buy_option_data['bid1'], buy_option_data['ask1']]),
                        synthetic_underlying, buy_symbol_option_info['strike_price'], maturity, r, q,
                        True if buy_symbol_option_info['call_put'] == 'C' else False)

    sell_iv, sell_delta, sell_gamma, sell_vega, sell_theta = \
        cal_implied_vol(np.array([sell_option_data['mid'], sell_option_data['bid1'], sell_option_data['ask1']]),
                        synthetic_underlying, sell_symbol_option_info['strike_price'], maturity, r, q,
                        True if sell_symbol_option_info['call_put'] == 'C' else False)

    data_return = {
        'status': True,
        'time': (pd.to_datetime(time) - pd.to_datetime('1970-01-01')) // pd.to_timedelta('1ms'),
        'synthetic': np.round(synthetic_underlying, 4),
        'vol_diff': np.round(buy_iv[0] - sell_iv[0], 2),
        'buy': {
            'bid1': buy_option_data['bid1'],
            'bidIV1': buy_iv[1],
            'bidVolume1': buy_option_data['bidVolume1'],
            'ask1': buy_option_data['ask1'],
            'askIV1': buy_iv[2],
            'askVolume1': buy_option_data['askVolume1'],
            'delta': buy_delta[0],
            'gamma': buy_gamma[0],
            'theta': buy_theta[0],
            'vega': buy_vega[0]
        },
        'sell': {
            'bid1': sell_option_data['bid1'],
            'bidIV1': sell_iv[1],
            'bidVolume1': sell_option_data['bidVolume1'],
            'ask1': sell_option_data['ask1'],
            'askIV1': sell_iv[2],
            'askVolume1': sell_option_data['askVolume1'],
            'delta': sell_delta[0],
            'gamma': sell_gamma[0],
            'theta': sell_theta[0],
            'vega': sell_vega[0]
        },
    }
    return jsonify(data_return)


@app.route('/data/ts/iv')
def _iv():
    offset = int(request.args.get('offset'))
    call_symbol, put_symbol = request.args.get('callSymbol'), request.args.get('putSymbol')
    call_symbol_option_info = option_info.get_option_info(call_symbol)
    put_symbol_option_info = option_info.get_option_info(put_symbol)

    syn_strike = syn_dct[put_symbol_option_info['underlying']][put_symbol_option_info['last_trading_day']]
    syn_symbol = option_info.get_parity(call_symbol_option_info['underlying'], syn_strike,
                                        call_symbol_option_info['last_trading_day'])

    df_call = db.get_minute_data_by_symbol(trading_day_offset(today, offset), syn_symbol[0])
    df_put = db.get_minute_data_by_symbol(trading_day_offset(today, offset), syn_symbol[1])
    
    df_call['mid'].loc[(df_call['bid1'] == df_call['ask1']) | (df_call['bid1'] <= 0) | (df_call['ask1'] <= 0)] = np.nan
    df_put['mid'].loc[(df_put['bid1'] == df_put['ask1']) | (df_put['bid1'] <= 0) | (df_put['ask1'] <= 0)] = np.nan
    
    maturity = cal_maturity(call_symbol_option_info['last_trading_day'], df_call.index)
    synthetic_underlying = df_call['mid'] + syn_strike * np.exp(-r * maturity) - df_put['mid']
    synthetic_underlying = synthetic_underlying.between_time('9:30:00', '15:00:00')

    df_call, df_put, df_underlying = \
        db.get_minute_data_parity(trading_day_offset(today, offset),
                                  call_symbol_option_info['underlying'],
                                  call_symbol_option_info['strike_price'],
                                  call_symbol_option_info['last_trading_day'])
    df_underlying = df_underlying.between_time('9:30:00', '15:00:00')
    df_call = df_call.between_time('9:30:00', '15:00:00')
    df_put = df_put.between_time('9:30:00', '15:00:00')

    basis = df_call['mid'] + call_symbol_option_info['strike_price'] - df_put['mid'] - df_underlying['mid']

    if offset == 0:
        df_underlying = pd.DataFrame(df_underlying, index=idx_trading_time)
    # rv[:30] = np.nan

    # rv2[:30] = np.nan

    buy_strike = call_symbol_option_info['strike_price']
    buy_type = call_symbol_option_info['call_put']
    # df_call = db.get_minute_data_by_symbol(trading_day_offset(today, offset), call_symbol)
    call_bid_iv = cal_implied_vol(df_call['bid1'], synthetic_underlying, float(buy_strike), maturity, r, q,
                                  True if buy_type == 'C' else False)[0]
    call_ask_iv = cal_implied_vol(df_call['ask1'], synthetic_underlying, float(buy_strike), maturity, r, q,
                                  True if buy_type == 'C' else False)[0]
    call_bid_iv = np.where(call_bid_iv == 0, np.nan, call_bid_iv)
    call_ask_iv = np.where(call_ask_iv == 0, np.nan, call_ask_iv)

    sell_strike = put_symbol_option_info['strike_price']
    sell_type = put_symbol_option_info['call_put']
    # df_put = db.get_minute_data_by_symbol(trading_day_offset(today, offset), put_symbol)
    put_bid_iv = cal_implied_vol(df_put['bid1'], synthetic_underlying, float(sell_strike), maturity, r, q,
                                 True if sell_type == 'C' else False)[0]
    put_ask_iv = cal_implied_vol(df_put['ask1'], synthetic_underlying, float(sell_strike), maturity, r, q,
                                 True if sell_type == 'C' else False)[0]
    put_bid_iv = np.where(put_bid_iv == 0, np.nan, put_bid_iv)
    put_ask_iv = np.where(put_ask_iv == 0, np.nan, put_ask_iv)

    df = pd.DataFrame({'vol': np.round((np.fmax(call_bid_iv, put_bid_iv) + np.fmin(call_ask_iv, put_ask_iv)) / 2, 2),
                       'synthetic': np.round(synthetic_underlying, 4),
                       'basis': np.round(basis, 4) * 10000
                       })
    if offset == 0:
        df = pd.DataFrame(df, index=idx_trading_time)

    df_last_underlying = db.get_underlying_minute_data(trading_day_offset(today, offset + 1),
                                                       call_symbol_option_info['underlying'])
    df_rv_underlying = pd.concat(
        [df_last_underlying, df_underlying], axis=0)
    df_rv_underlying = df_rv_underlying.between_time('9:30:00', '15:00:00')
    df_rv = np.round(
        np.sqrt((np.log(df_rv_underlying['mid']).diff() ** 2).rolling(len(df_last_underlying)).sum() * 244) * 100, 2)
    df['rv'] = df_rv[-len(df_last_underlying):]
    # df['rv'] = np.round(np.sqrt((np.log(df_underlying['mid']).diff() ** 2).cumsum() * (df.shape[0] / np.arange(1, df.shape[0] + 1, 1) * 244)) * 100, 2)
    df['rv2'] = np.round(np.sqrt((np.log(df_underlying['mid']).diff() ** 2).cumsum() * 244) * 100, 2)
    # 'rv': np.round(rv, 2)
    # 'basis': np.round(basis, 4) * 10000
    # print(df_put[['bid1', 'ask1']])
    # df['vol'] = np.where(check_data(df_call['bid1'], df_call['ask1']) | check_data(df_put['bid1'], df_put['ask1']),
    #                      np.nan, df['vol'])
    df = df.between_time('9:31:00', '14:56:00')
    return df.to_json(orient='split')


@app.route('/data/snapshot/iv')
def _snap_shot_iv():
    call_symbol, put_symbol = request.args.get('callSymbol'), request.args.get('putSymbol')

    call_option_data = c.get_market_data(call_symbol)
    if (not call_option_data) or (call_option_data['ask1'] == 0):
        return jsonify({'status': False})

    put_option_data = c.get_market_data(put_symbol)
    if not put_option_data:
        return jsonify({'status': False})

    call_symbol_option_info = option_info.get_option_info(call_symbol)
    put_symbol_option_info = option_info.get_option_info(put_symbol)
    time = call_option_data['time']
    maturity = cal_maturity(call_symbol_option_info['last_trading_day'], time)

    syn_strike = syn_dct[put_symbol_option_info['underlying']][put_symbol_option_info['last_trading_day']]
    syn_symbol = option_info.get_parity(call_symbol_option_info['underlying'], syn_strike, call_symbol_option_info['last_trading_day'])
    syn_buy_data = c.get_market_data(syn_symbol[0])
    syn_sell_data = c.get_market_data(syn_symbol[1])
    if not syn_buy_data:
        return jsonify({'status': False})
    if not syn_sell_data:
        return jsonify({'status': False})
    synthetic_underlying = syn_buy_data['mid'] + syn_strike * np.exp(-r * maturity) - syn_sell_data['mid']

    underlying_symbol = call_symbol_option_info['underlying']
    underlying_data = c.get_market_data(underlying_symbol)

    if not underlying_data:
        return jsonify({'status': False})
    basis = call_option_data['mid'] + call_symbol_option_info['strike_price'] - put_option_data['mid'] - underlying_data['mid']

    call_iv, delta_call, gamma, vega, theta = \
        cal_implied_vol(np.array([call_option_data['mid'], call_option_data['bid1'], call_option_data['ask1']]),
                        synthetic_underlying, call_symbol_option_info['strike_price'], maturity, r, q,
                        True if call_symbol_option_info['call_put'] == 'C' else False)

    put_iv, delta_put, _, _, _ = \
        cal_implied_vol(np.array([put_option_data['mid'], put_option_data['bid1'], put_option_data['ask1']]),
                        synthetic_underlying, put_symbol_option_info['strike_price'], maturity, r, q,
                        True if put_symbol_option_info['call_put'] == 'C' else False)

    data_return = {
        'status': True,
        'time': (pd.to_datetime(time) - pd.to_datetime('1970-01-01')) // pd.to_timedelta('1ms'),
        'underlying': underlying_data['last'],
        'basis': np.round(basis, 4) * 10000,
        'synthetic': np.round(synthetic_underlying, 4),
        'vol': np.round((np.maximum(call_iv[1], put_iv[1]) + np.minimum(call_iv[2], put_iv[2])) / 2, 2),
        'rv': {
            'rv': 0.0,
            'rvEst': 0.0
        },
        'call': {
            'last': call_option_data['last'],
            'iv': call_iv[0],
            'bid1': call_option_data['bid1'],
            'bidIV1': call_iv[1],
            'bidVolume1': call_option_data['bidVolume1'],
            'ask1': call_option_data['ask1'],
            'askIV1': call_iv[2],
            'askVolume1': call_option_data['askVolume1'],
        },
        'put': {
            'last': put_option_data['last'],
            'iv': put_iv[0],
            'bid1': put_option_data['bid1'],
            'bidIV1': put_iv[1],
            'bidVolume1': put_option_data['bidVolume1'],
            'ask1': put_option_data['ask1'],
            'askIV1': put_iv[2],
            'askVolume1': put_option_data['askVolume1'],
        },
        'greeks': {
            'delta': np.minimum(delta_call[0], np.abs(delta_put[0])),
            'vega': vega[0],
            'gamma': gamma[0],
            'theta': theta[0],
        },
    }
    return jsonify(data_return)


if __name__ == '__main__':
    app.run(host='10.21.78.53')
    # app.run()

