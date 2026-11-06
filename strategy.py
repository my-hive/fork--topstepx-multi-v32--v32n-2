"""Micro-equity opening-return cross-sectional reversion, flat 14:00 CT."""
import numpy as np
import pandas as pd

_SPECS = {'MES': (5., .25, .75), 'MNQ': (2., .25, .75),
          'MYM': (.5, 1., .75), 'M2K': (5., .1, .75)}


def _risk(df, symbol):
    pv, tick, fee = _SPECS[symbol]
    close = df.close.to_numpy()
    prev = np.r_[close[0], close[:-1]]
    tr = np.maximum(df.high.to_numpy() - df.low.to_numpy(),
                    np.maximum(abs(df.high.to_numpy() - prev), abs(df.low.to_numpy() - prev)))
    atr = df.assign(_tr=tr).groupby('session', sort=False)._tr.transform(
        lambda x: x.rolling(20, min_periods=20).mean()).to_numpy()
    return np.nan_to_num(1.5 * atr * pv + 4 * tick * pv + 3 * fee, nan=0.)


def entry_risk(panel):
    return {s: _risk(df, s) for s, df in panel.items()}


def signals(panel):
    result = {s: np.zeros(len(df), dtype=np.int64) for s, df in panel.items()}
    if not set(panel) <= set(_SPECS):
        return result
    returns, risks = {}, {}
    for symbol, df in panel.items():
        sec = df.ct_sec.to_numpy()
        session = df.session.astype(str).to_numpy()
        entry = sec == 36000
        reference = pd.Series(np.where(sec == 30600, df.open, np.nan), index=df.index).groupby(session).transform('first')
        ret = df.close.to_numpy() / reference.to_numpy() - 1
        returns[symbol] = pd.Series(ret[entry], index=session[entry])
        risks[symbol] = pd.Series(_risk(df, symbol)[entry], index=session[entry])
    returns, risks = pd.DataFrame(returns).dropna(), pd.DataFrame(risks).dropna()
    common = returns.index.intersection(risks.index)
    for session in common:
        long, short = returns.loc[session].idxmin(), returns.loc[session].idxmax()
        if risks.loc[session, long] + risks.loc[session, short] > 300:
            continue
        for symbol, side in ((long, 1), (short, -1)):
            df = panel[symbol]
            sec = df.ct_sec.to_numpy()
            sessions = df.session.astype(str).to_numpy()
            times = df.index.as_unit('ns').asi8
            out = result[symbol]
            indices = np.flatnonzero(sessions == session)
            active, entered, last = 0, False, None
            for j in indices:
                if last is not None and times[j] - times[last] != 60_000_000_000:
                    active = 0
                if sec[j] >= 50400:
                    active = 0
                elif active:
                    out[j] = active
                elif not entered and sec[j] == 36000:
                    out[j] = active = side
                    entered = True
                last = j
    return result
