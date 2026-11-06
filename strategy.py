"""Opening-range sweep continuation after 10:00 CT, flat 14:00."""
import numpy as np

# point value, tick, estimated commission; selected liquid development sleeves.
_SPECS = {
    'MES': (5., .25, .75),
    'M2K': (5., .1, .75),
    'MGC': (10., .1, .75),
    'MCL': (100., .01, .75),
}


def _risk(df, symbol):
    pv, tick, fee = _SPECS[symbol]
    close = df.close.to_numpy()
    prev = np.r_[close[0], close[:-1]]
    tr = np.maximum(df.high.to_numpy() - df.low.to_numpy(),
                    np.maximum(abs(df.high.to_numpy() - prev), abs(df.low.to_numpy() - prev)))
    atr = df.assign(_tr=tr).groupby('session', sort=False)._tr.transform(
        lambda x: x.rolling(20, min_periods=20).mean()).to_numpy()
    # Warmup cannot enter; neutral finite declaration satisfies the risk contract.
    return np.nan_to_num(1.5 * atr * pv + 4 * tick * pv + 3 * fee, nan=0.)


def entry_risk(panel):
    return {s: _risk(df, s) for s, df in panel.items()}


def signals(panel):
    result = {}
    for symbol, df in panel.items():
        out = np.zeros(len(df), dtype=np.int64)
        if symbol not in _SPECS:
            result[symbol] = out
            continue
        risk = _risk(df, symbol)
        high, low, close = (df[x].to_numpy() for x in ('high', 'low', 'close'))
        sec = df.ct_sec.to_numpy()
        for indices in df.groupby('session', sort=False).indices.values():
            opening = (sec[indices] >= 30600) & (sec[indices] < 36000)
            if not opening.any():
                continue
            hi = high[indices][opening].max()
            lo = low[indices][opening].min()
            active = 0
            for j in indices:
                if sec[j] >= 50400:
                    active = 0
                elif active:
                    out[j] = active
                elif 36000 <= sec[j] < 48600 and risk[j] <= 300:
                    side = (-1 if low[j] < lo < close[j] else
                            1 if high[j] > hi > close[j] else 0)
                    if side:
                        out[j] = active = side
        result[symbol] = out
    return result
