"""Post-10:00 CT opening-move reversion in heating oil, flat 14:00."""
import numpy as np

_PV, _TICK, _FEE = 42000., .0001, 2.5


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
        if symbol != 'HO':
            result[symbol] = out
            continue
        risk = _risk(df)
        sec = df.ct_sec.to_numpy()
        for indices in df.groupby('session', sort=False).indices.values():
            local_sec = sec[indices]
            opening = np.flatnonzero((local_sec >= 30600) & (local_sec < 36000))
            entry = np.flatnonzero(local_sec == 36000)
            exit_ = np.flatnonzero(local_sec == 50400)
            if not len(opening) or not len(entry) or not len(exit_):
                continue
            j, k = entry[0], exit_[0]
            if j >= k or risk[indices[j]] > 300:
                continue
            move = df.close.to_numpy()[indices[j]] - df.open.to_numpy()[indices[opening[0]]]
            if move:
                out[indices[j:k]] = -int(np.sign(move))
        result[symbol] = out
    return result
