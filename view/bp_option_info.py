import numpy as np
from flask import Blueprint, jsonify, request
from model.option_info import option_info

bp_option_info = Blueprint('bp_option_info', __name__)


@bp_option_info.route('/data/option_info/get_last_trading_day/<underlying>')
def get_last_trading_day(underlying):
    arr_last_trading_day = option_info.get_last_trading_day_array(underlying)
    arr_strike = option_info.get_strike_price_arr(underlying, arr_last_trading_day[0])
    return jsonify({"arrLastTradingDay": np.datetime_as_string(arr_last_trading_day, unit='D').tolist(), "arrStrike": arr_strike.tolist()})


@bp_option_info.route('/data/option_info/get_strike/<underlying>/<last_trading_day>')
def get_strike(underlying, last_trading_day):
    arr_strike = option_info.get_strike_price_arr(underlying, last_trading_day)
    return jsonify(arr_strike.tolist())


@bp_option_info.route('/data/option_info/get_next_strike')
def get_next_strike():
    return chg_strike_or_month(request.args, option_info.get_next_strike)


@bp_option_info.route('/data/option_info/get_next_month')
def get_next_month():
    return chg_strike_or_month(request.args, option_info.get_next_month)


def chg_strike_or_month(params, func):
    underlying = params.get('underlying')
    month = int(params.get('month'))
    strike = float(params.get('strike'))
    nxt = int(params.get('next'))

    month, strike, last_trading_day, call_symbol, put_symbol = func(underlying, month, strike, nxt)
    dct = {'underlying': underlying, 'strike': strike,
           'lastTradingDay': last_trading_day.strftime('%m-%d'), 'month': month,
           'callSymbol': call_symbol, 'putSymbol': put_symbol}
    return jsonify(dct)

