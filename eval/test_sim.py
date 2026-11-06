"""Runnable without pytest: python eval/test_sim.py."""
import importlib.util
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
from sim import (run_days, attempts, score, validate_panel, validate_targets,
                 lookahead_check, permute_targets, load_panel, main, economic_eligibility,
                 validate_entry_risk)
from instruments import SPECS


def frame(times=None, prices=None, symbol='MES'):
    index = pd.DatetimeIndex(times if times is not None else pd.date_range('2024-01-02 16:00', periods=4, freq='min', tz='UTC'), name='ts')
    values = np.asarray(prices if prices is not None else [100., 100., 105., 110.])
    ct = index.tz_convert('America/Chicago')
    return pd.DataFrame({'open': values, 'high': values + 1, 'low': values - 1, 'close': values,
                         'volume': 10, 'contract': symbol + 'H4', 'session': '2024-01-02',
                         'ct_sec': ct.hour * 3600 + ct.minute * 60}, index=index)


def rejects(fn):
    try:
        fn()
    except (ValueError, AssertionError):
        return
    raise AssertionError('expected rejection')


def check():
    df = frame()
    target = {'MES': np.array([1, 1, 0, 0])}
    r = run_days({'MES': df}, target, stressed=False, ledger=True)
    fills = r['ledger']
    assert len(fills) == 2 and fills[0]['timestamp'] == df.index[1].isoformat()
    assert fills[0]['position_after'] == 1 and fills[1]['timestamp'] == df.index[3].isoformat()
    assert fills[0]['price'] == 100.25 and fills[1]['price'] == 109.75
    assert abs(r['days'][0]['pnl'] - (9.5 * 5 - 1.5)) < 1e-9
    assert abs(sum(f['realized_pnl'] - f['commission'] for f in fills) - r['days'][0]['pnl']) < 1e-9
    assert run_days({'MES': df}, target)['days'][0]['pnl'] < r['days'][0]['pnl']
    # No same bar, last-bar target never fills.
    r = run_days({'MES': df}, {'MES': np.array([0, 0, 0, 1])}, ledger=True)
    assert not r['ledger']
    # Same account, integer holdings, simultaneous exposure rejected not prioritized.
    panel = {'MES': df, 'MGC': frame(symbol='MGC')}
    rejects(lambda: run_days(panel, {s: np.full(4, 30) for s in panel}))
    r = run_days(panel, {s: np.full(4, 20) for s in panel}, ledger=True)
    assert r['max_exposure'] == 4 and all(isinstance(x['position_after'], int) for x in r['ledger'])
    assert abs(sum(r['per_market'][s]['pnl'] for s in panel) - r['days'][0]['pnl']) < 1e-8
    # Gap/roll closes at prior close; no pending carry to disconnected open.
    gap = frame(times=pd.to_datetime(['2024-01-02 16:00Z', '2024-01-02 16:01Z', '2024-01-02 16:10Z', '2024-01-02 16:11Z']))
    r = run_days({'MES': gap}, {'MES': np.ones(4, dtype=int)}, ledger=True)
    assert r['ledger'][1]['reason'] == 'gap_or_roll'
    assert r['ledger'][1]['timestamp'] == '2024-01-02T16:02:00+00:00'
    assert not any(x['timestamp'] == gap.index[2].isoformat() for x in r['ledger'])
    roll = df.copy()
    roll.loc[roll.index[2]:, 'contract'] = 'MESM4'
    r = run_days({'MES': roll}, {'MES': np.ones(4, dtype=int)}, ledger=True)
    assert r['ledger'][1]['contract'] == 'MESH4' and r['ledger'][1]['reason'] == 'gap_or_roll'
    # DLL gap overshoots; no magical -1000 fill, shared lock forbids later entries.
    crash = frame(prices=[100., 100., 50., 50.])
    r = run_days({'MES': crash}, {'MES': np.full(4, 10)}, ledger=True)
    assert r['days'][0]['pnl'] < -2500 and r['ledger'][-1]['reason'] == 'dll_gap'
    assert len(r['ledger']) == 2
    # Intrabar multiasset DLL uses sum adverse extremes, not independent asset limits.
    d1, d2 = frame(), frame(symbol='MGC')
    d1.loc[d1.index[1], 'low'] = 80
    d2.loc[d2.index[1], 'low'] = 90
    r = run_days({'MES': d1, 'MGC': d2}, {'MES': np.full(4, 5), 'MGC': np.full(4, 5)}, ledger=True)
    assert r['days'][0]['pnl'] < -1000 and sum(f['reason'] == 'dll_intrabar' for f in r['ledger']) == 2
    # 15:10 flat, no opening until 17:00. Target close at 17:00 fills 17:01.
    evening = frame(times=pd.to_datetime(['2024-01-02 21:08Z', '2024-01-02 21:09Z', '2024-01-02 21:10Z', '2024-01-02 21:11Z']))
    r = run_days({'MES': evening}, {'MES': np.ones(4, dtype=int)}, ledger=True)
    assert r['ledger'][1]['timestamp'] == '2024-01-02T21:10:00+00:00'
    assert len(r['ledger']) == 2
    overnight = frame(times=pd.date_range('2024-01-02 22:59Z', periods=4, freq='min'))
    r = run_days({'MES': overnight}, {'MES': np.ones(4, dtype=int)}, ledger=True)
    assert r['ledger'][0]['timestamp'] == '2024-01-02T23:00:00+00:00'
    # Timestamp source CT timezone, including DST, not UTC hour or process TZ.
    summer = frame(times=pd.date_range('2024-07-02 20:08Z', periods=4, freq='min'))
    summer['session'] = '2024-07-02'
    r = run_days({'MES': summer}, {'MES': np.ones(4, dtype=int)}, ledger=True)
    assert r['ledger'][1]['timestamp'] == '2024-07-02T20:10:00+00:00'
    broken = df.copy(); broken['ct_sec'] = 0
    rejects(lambda: validate_panel({'MES': broken}))
    rejects(lambda: validate_targets({'MES': df}, {'XYZ': np.zeros(4, int)}))
    for values in ([0., 0., np.nan, 0.], [0., 0., 0., 0.], [1, 2], [[1], [2], [3], [4]]):
        rejects(lambda: validate_targets({'MES': df}, {'MES': values}))
    old = frame(times=pd.date_range('2010-01-02 16:00Z', periods=4, freq='min'))
    rejects(lambda: validate_panel({'MES': old}))
    assert SPECS['QM'].weight == .5 and SPECS['QG'].weight == .25 and SPECS['SIL'].weight == .2
    # strict consistency, minimum trading days and EOD trailing floor.
    days = [{'session': f'2024-01-{i+1:02}', 'pnl': 1000., 'minimum': 0., 'traded': True} for i in range(30)]
    assert attempts(days)[0]['passed'] and attempts(days)[0]['days'] == 3
    days[0]['pnl'] = 3000.
    for d in days[1:]: d['pnl'] = 0.
    assert not attempts(days)[0]['passed']
    days[1]['minimum'] = -3001.
    assert attempts(days)[0]['reason'] == 'mll'  # floor locked 50K after first +3K
    assert score(days)['yearly']['2024']['attempts'] == 1
    # Prefix causality, common cutoffs across uneven sparse markets.
    spec = importlib.util.spec_from_file_location('baseline', Path(__file__).parents[1] / 'strategy.py')
    baseline = importlib.util.module_from_spec(spec); spec.loader.exec_module(baseline)
    lookahead_check(baseline.signals, panel)
    rejects(lambda: lookahead_check(lambda p: {s: np.full(len(d), len(d), dtype=int) for s, d in p.items()}, panel))
    permuted = permute_targets(panel, {s: np.array([1, 1, -2, 0]) for s in panel}, 7)
    assert np.array_equal(abs(permuted['MES']), [1, 1, 2, 0])
    assert np.array_equal(permuted['MES'], permuted['MGC'])
    eligible = economic_eligibility([{'session': '2020-01-01', 'pnl': 1},
                                    {'session': '2021-01-01', 'pnl': 1},
                                    {'session': '2022-01-01', 'pnl': 1}], True, True,
                                   {'p_value': .01})
    assert eligible['passed']
    assert economic_eligibility([{'session': '2020-01-01', 'pnl': 1}], True, True,
                                {'p_value': .01})['passed']
    assert economic_eligibility([{'session': '2024-01-01', 'pnl': 1},
                                 {'session': '2025-01-01', 'pnl': 1}], True, True,
                                {'p_value': .01})['passed']
    assert not economic_eligibility([{'session': '2024-01-01', 'pnl': 1},
                                     {'session': '2025-01-01', 'pnl': -1}], True, True,
                                    {'p_value': .01})['passed']
    assert validate_entry_risk({'MES': df}, {'MES': np.zeros(len(df))})['MES'].sum() == 0
    rejects(lambda: validate_entry_risk({'MES': df}, {'MES': np.full(len(df), -1.)}))
    risky = run_days({'MES': df}, {'MES': np.array([0, 2, 0, 0])},
                     entry_risk={'MES': np.full(len(df), 151.)})
    assert not risky['entry_risk_pass'] and risky['max_entry_risk'] == 302
    # CLI and machine report/ledger integration without modifying repository root.
    import subprocess, sys
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        for s, d in panel.items():
            d.to_parquet(root/f'{s}.parquet')
        loaded = load_panel(root, list(panel))
        assert len(loaded) == 2
        strategy = root/'candidate.py'
        strategy.write_text('import numpy as np\ndef signals(panel):\n return {s: (np.arange(len(d)) < 2).astype(int) for s,d in panel.items()}\n')
        subprocess.run([sys.executable, str(Path(__file__).with_name('sim.py')), '--data', temp, '--symbols', 'MES', 'MGC', '--strategy', str(strategy), '--output', str(root/'report.json'), '--ledger', str(root/'fills.jsonl'), '--null-seeds', '200'], check=True)
        import json
        report = json.loads((root/'report.json').read_text())
        assert report['schema_version'] == 2 and len((root/'fills.jsonl').read_text().splitlines()) == 4
        assert 'eligibility' in report['stressed']
        assert report['null']['seeds'] == 200
    reversal = run_days({'MES': frame(prices=[100., 100., 105., 110.])},
                        {'MES': np.array([1, -1, 0, 0])}, stressed=False, ledger=True)
    ledger_net = sum(f['realized_pnl'] - f['commission'] for f in reversal['ledger'])
    assert abs(reversal['days'][0]['pnl'] - ledger_net) < 1e-8
    assert abs(ledger_net - (-8.0)) < 1e-8
    print('multiasset simulator self-check ok')


if __name__ == '__main__':
    check()
