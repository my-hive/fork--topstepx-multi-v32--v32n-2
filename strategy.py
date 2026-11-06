"""M2K failed-auction reversion with causal stop and midpoint target."""
import numpy as np

_PV, _TICK, _FEE = 5., .1, .75


def _atr(df):
    close = df.close.to_numpy()
    prev = np.r_[close[0], close[:-1]]
    tr = np.maximum(df.high.to_numpy() - df.low.to_numpy(),
                    np.maximum(abs(df.high.to_numpy() - prev), abs(df.low.to_numpy() - prev)))
    return df.assign(_tr=tr).groupby('session', sort=False)._tr.transform(
        lambda x: x.rolling(20, min_periods=20).mean()).to_numpy()


def entry_risk(panel):
    result = {}
    for symbol, df in panel.items():
        risk = 1.5 * _atr(df) * _PV + 4 * _TICK * _PV + 3 * _FEE
        result[symbol] = np.nan_to_num(risk, nan=0.)
    return result


def signals(panel):
    result = {}
    for symbol, df in panel.items():
        out = np.zeros(len(df), dtype=np.int64)
        if symbol != 'M2K':
            result[symbol] = out
            continue
        high, low, close = (df[x].to_numpy() for x in ('high', 'low', 'close'))
        sec = df.ct_sec.to_numpy()
        atr = _atr(df)
        times = df.index.as_unit('ns').asi8
        for indices in df.groupby('session', sort=False).indices.values():
            opening = (sec[indices] >= 30600) & (sec[indices] < 36000)
            if not opening.any():
                continue
            hi, lo = high[indices][opening].max(), low[indices][opening].min()
            mid = (hi + lo) / 2
            active, entered, last = 0, False, None
            stop = target = 0.
            for j in indices:
                if last is not None and times[j] - times[last] != 60_000_000_000:
                    active = 0
                if sec[j] >= 50400:
                    active = 0
                elif active:
                    hit_stop = low[j] <= stop if active == 1 else high[j] >= stop
                    hit_target = high[j] >= target if active == 1 else low[j] <= target
                    if not hit_stop and not hit_target:
                        out[j] = active
                    else:
                        active = 0
                elif (not entered and 36000 <= sec[j] < 50400 and np.isfinite(atr[j])
                      and 1.5 * atr[j] * _PV + 4 * _TICK * _PV + 3 * _FEE <= 300):
                    side = 1 if low[j] < lo < close[j] else (-1 if high[j] > hi > close[j] else 0)
                    if side and (mid > close[j] if side == 1 else mid < close[j]):
                        active = side
                        out[j] = side
                        stop = close[j] - side * 1.5 * atr[j]
                        target = mid
                        entered = True
                last = j
        result[symbol] = out
    return result
