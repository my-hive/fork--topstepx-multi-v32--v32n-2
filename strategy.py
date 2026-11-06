"""CL large first-30-minute RTH move reversion, flat 14:00 CT."""
from collections import deque
import numpy as np

_PV, _TICK, _FEE = 1000., .01, 2.5


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
        if symbol != 'CL':
            result[symbol] = out
            continue
        sec, risk = df.ct_sec.to_numpy(), _risk(df)
        open_, high, low, close = (df[x].to_numpy() for x in ('open', 'high', 'low', 'close'))
        times = df.index.as_unit('ns').asi8
        history, previous_rth_close = deque(maxlen=20), None
        for indices in df.groupby('session', sort=False).indices.values():
            local_sec = sec[indices]
            opening = np.flatnonzero(local_sec == 30600)
            daily_atr = np.mean(history) if len(history) == 20 else np.nan
            active, entered, last = 0, False, None
            for j in indices:
                if last is not None and times[j] - times[last] != 60_000_000_000:
                    active = 0
                if sec[j] >= 50400:
                    active = 0
                elif active:
                    out[j] = active
                elif not entered and sec[j] == 34140 and len(opening) and risk[j] <= 300:
                    move = close[j] - open_[indices[opening[0]]]
                    if np.isfinite(daily_atr) and abs(move) >= 1.0 * daily_atr and move:
                        out[j] = active = -int(np.sign(move))
                        entered = True
                last = j
            rth = (local_sec >= 30600) & (local_sec < 54540)
            if rth.any():
                rh = high[indices][rth].max()
                rl = low[indices][rth].min()
                rc = close[indices][rth][-1]
                if previous_rth_close is not None:
                    history.append(max(rh - rl, abs(rh - previous_rth_close), abs(rl - previous_rth_close)))
                previous_rth_close = rc
        result[symbol] = out
    return result
