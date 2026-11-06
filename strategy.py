"""Causal baseline, optional symbols. No requirement to manufacture market diversity.
Slow 20-bar momentum, entries after 10:00 CT, flat at 14:00. Not claimed profitable.
"""
import numpy as np


def entry_risk(panel):
    return {symbol: np.zeros(len(df)) for symbol, df in panel.items()}


def signals(panel):
    result = {}
    for symbol, df in panel.items():
        out = np.zeros(len(df), dtype=np.int64)
        # Two micros only, at most 0.2 standard equivalents total.
        if symbol not in ('MES', 'MGC'):
            result[symbol] = out
            continue
        for indices in df.groupby('session', sort=False).indices.values():
            close = df.close.to_numpy()[indices]
            sec = df.ct_sec.to_numpy()[indices]
            # Rolling mean excludes future rows; warmup restarts each session.
            for j in range(20, len(indices)):
                if 36000 <= sec[j] < 50400:
                    out[indices[j]] = int(np.sign(close[j] - close[j-20:j].mean()))
        result[symbol] = out
    return result
