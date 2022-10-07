import numpy as np
import model.pricing.BlackScholes as bs


def cal_implied_vol(v, S, K, T, r, q, is_call, greeks=False, error=0.000001):
    v = _checkType(v)
    length = v.shape[0]

    S = _checkType(S, length)
    K = _checkType(K, length)
    T = _checkType(T, length)
    r = _checkType(r, length)
    q = _checkType(q, length)
    is_call = _checkType(is_call, length, dtype=np.int32)

    ret = bs.calImpliedVol(v, S, K, T, r, q, is_call, greeks, error)
    iv, delta, gamma, vega, theta = ret
    iv = np.round(iv * 100, 2)
    delta = np.round(delta, 2)
    gamma = np.round(gamma * S / 100, 2)
    theta = -np.round(theta * 10000 / 244, 2)
    vega = np.round(vega * 10000 / 100, 2)
    return iv, delta, gamma, vega, theta


def _checkType(x, length=1, dtype=np.float64):
    if np.isscalar(x):
        return np.full(length, x, dtype=dtype)
    # elif type(x) is Series:
    #     return x.astype(dtype).to_numpy()
    return np.asarray(x, dtype=dtype)


if __name__ == '__main__':
    print(cal_implied_vol(0.1805, 5.13, 5.25, 0.05, 0.03, 0.03, True))
