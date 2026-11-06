# TopstepX multi-asset v3.2

Causal intraday CME 1-minute research. Agents see development data only. Sealed validator sees validation. Historical OOS stays owner-only and untouched.

## Fast development screen

```bash
python3 /opt/v32-eval/eval/sim.py \
  --data /data/dev --symbols MES MGC \
  --strategy "$PWD/strategy.py" --output report.json --ledger fills.jsonl \
  --null-seeds 0
```

Screen reports economics and risk but has zero eligibility score until 200-seed test. Every strategy needs `signals(panel)` and `entry_risk(panel)`. Risk declaration is causal dollars per contract; any entry above $300 fails.

## Frozen finalist

Freeze source first. Then run once:

```bash
python3 /opt/v32-eval/eval/sim.py \
  --data /data/dev --symbols MES MGC \
  --strategy "$PWD/strategy.py" --output finalist.json --null-seeds 200
```

Eligibility needs positive PnL in every year present, entry diversity, risk cap, and directional-null `p <= 0.05`.

## Sealed validation

```bash
python3 /usr/local/bin/v32-validate --strategy strategy.py --symbols MNQ,MCL
```

Receipt means queued/finished execution only. It never means pass.

Read `program.md` before research.
