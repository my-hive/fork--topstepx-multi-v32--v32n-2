"""RB low-volume first-30-minute move reversion after 10:00 CT."""
from collections import deque
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
        if symbol != 'RB':
            result[symbol] = out
            continue
        sec, risk = df.ct_sec.to_numpy(), _risk(df)
        open_, close, volume = (df[x].to_numpy() for x in ('open', 'close', 'volume'))
        times = df.index.as_unit('ns').asi8
        history = deque(maxlen=20)
        for indices in df.groupby('session', sort=False).indices.values():
            local_sec = sec[indices]
            opening = np.flatnonzero((local_sec >= 30600) & (local_sec < 34200))
            opening_volume = volume[indices][opening].sum() if len(opening) else np.nan
            volume_median = np.median(history) if len(history) == 20 else np.nan
            active, entered, last = 0, False, None
            early_move = None
            for j in indices:
                if sec[j] == 34140 and len(opening):
                    early_move = close[j] - open_[indices[opening[0]]]
                if last is not None and times[j] - times[last] != 60_000_000_000:
                    active = 0
                if sec[j] >= 50400:
                    active = 0
                elif active:
                    out[j] = active
                elif not entered and sec[j] == 36000 and early_move and risk[j] <= 300:
                    if np.isfinite(volume_median) and opening_volume <= volume_median:
                        out[j] = active = -int(np.sign(early_move))
                        entered = True
                last = j
            if len(opening):
                history.append(opening_volume)
        result[symbol] = out
    return result
