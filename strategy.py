"""MYM overnight-gap reversion after 10:00 CT, flat 14:00."""
import numpy as np

_PV, _TICK, _FEE = .5, 1., .75


def _risk(df):
    close = df.close.to_numpy()
    prev = np.r_[close[0], close[:-1]]
    tr = np.maximum(df.high.to_numpy() - df.low.to_numpy(),
                    np.maximum(abs(df.high.to_numpy() - prev), abs(df.low.to_numpy() - prev)))
    atr = df.assign(_tr=tr).groupby('session', sort=False)._tr.transform(
        lambda x: x.rolling(20, min_periods=20).mean()).to_numpy()
    return np.nan_to_num(1.5 * atr * _PV + 4 * _TICK * _PV + 3 * _FEE, nan=0.)


def entry_risk(panel):
    return {s: _risk(df) for s, df in panel.items()}


def signals(panel):
    result = {}
    for symbol, df in panel.items():
        out = np.zeros(len(df), dtype=np.int64)
        if symbol != 'MYM':
            result[symbol] = out
            continue
        sec, risk = df.ct_sec.to_numpy(), _risk(df)
        open_, close = df.open.to_numpy(), df.close.to_numpy()
        times = df.index.as_unit('ns').asi8
        previous_close = None
        for indices in df.groupby('session', sort=False).indices.values():
            opening = np.flatnonzero(sec[indices] == 30600)
            active, entered, last = 0, False, None
            for j in indices:
                if last is not None and times[j] - times[last] != 60_000_000_000:
                    active = 0
                if sec[j] >= 50400:
                    active = 0
                elif active:
                    out[j] = active
                elif (not entered and sec[j] == 36000 and previous_close is not None
                      and len(opening) and risk[j] <= 300):
                    gap = open_[indices[opening[0]]] - previous_close
                    if gap:
                        out[j] = active = -int(np.sign(gap))
                        entered = True
                last = j
            prior = np.flatnonzero(sec[indices] == 54600)
            if len(prior):
                previous_close = close[indices[prior[-1]]]
        result[symbol] = out
    return result
