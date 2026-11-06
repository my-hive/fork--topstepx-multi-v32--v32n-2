# TopstepX 50K multi-asset research v3.2

## Mission
Find causal intraday-only 1-minute CME futures strategies for one simulated TopstepX 50K combine account. Development evidence is not proof. Optimize economic edge first; combine pass rate ranks only eligible finalists.

## Account model
One shared $50,000 account. Target $3,000. Daily loss limit $1,000: evaluator flattens. EOD trailing maximum loss $2,000, locked at $50,000. At least two trading days. Best day under 50% total profit. Flat by 15:09 CT; no overnight positions. Integer positions only. Aggregate exposure at most 5 standard equivalents.

Each newly opened position needs a causal protective-stop risk declaration. `entry_risk(panel)` returns `{symbol: dollar-risk-per-contract array}` aligned with bars. Risk at entry is opened contracts times prior-bar declaration. Every entry must be at most $300. Missing declaration fails eligibility. Stop distance must exist before entry; no retrospective close-based stop.

## Universe and data
Use only cache-present CME roots: ES MES NQ MNQ YM MYM RTY M2K NKD; CL MCL QM NG MNG QG RB HO; GC MGC SI SIL HG MHG PL; 6E M6E 6B M6B 6A M6A 6C 6J 6S 6N 6M; MBT MET; ZB UB ZT ZF ZN TN; ZC ZS ZW ZL HE LE. History begins at actual product availability. Different sizes of same underlying are not independent evidence.

All stages use Databento 1-minute OHLCV, UTC bar-start timestamps. Completed-bar feature available only after close; signal fills next minute open. Development only: `/data/dev/<SYMBOL>.parquet`, 2010-06 through 2023-12. Sealed validation: 2024-01 through 2025-08, never mounted for agents. Historical audit: 2025-09 through 2026-08, owner-only reused data, not fresh OOS. No raw hidden data, old task history, host memory, hidden-period probing, external services, or live trading access.

## Strategy contract
`signals(panel)` receives `{symbol: pandas.DataFrame}` and returns aligned integer target arrays. Omitted symbols flat. `entry_risk(panel)` same keys, nonnegative finite dollar risk per contract. No future shifts, centered windows, full-sample normalization, cross-market leakage, fractional sleeves, calendar/date selection, or Kelly sizing selected from backtest wins. Lag trailing windows. Maximum six independent entry gates.

## Fast screen, then frozen finalist
Full 200-seed null run takes about one hour. Do not burn budget on it early.

1. Screen hypothesis with `--null-seeds 0`; inspect PnL, fills, costs, entry risk, yearly PnL, turnover, and mechanism.
2. Freeze source SHA after plausible screen. Run `--null-seeds 200` once. No parameter changes after seeing null result.
3. Only development-eligible frozen source may use sealed validation quota.

Screen output always has score zero because directional evidence is untested. That is expected. Do not treat it as failure.

## Eligibility
Evaluator uses stressed costs: 2 ticks slippage plus 1.5x estimated commission. New entries from 08:30–09:30 CT must not exceed 40%. Do not add correlated or losing sleeves to raise account variance.

Frozen candidate eligible only when every gate passes:

1. Positive total stressed PnL.
2. Positive stressed PnL in every calendar year present in evaluated partition. Validation has 2024 plus partial 2025, so both must be positive; no impossible three-year rule.
3. Entry-time diversity passes.
4. Every entry risk is at most $300.
5. Account-pass score beats 200 frozen whole-session shared-side randomizations at `p <= 0.05`.

Randomized-side null preserves exact entries, exits, sizes, timing, costs, and flat behavior. It flips entire session direction randomly. It tests whether strategy direction predicts price direction. If random signs match or beat candidate more than 5% of runs, positive PnL can be market drift or timing exposure, not directional edge.

Ineligible score is zero. Eligible candidates rank by mean worst three yearly rolling-30-session pass rates. Report raw score plus every gate. Never claim edge from raw score alone.

## Experiment budget
At most 30 recorded development experiments per agent. Every change, crash, screen, or variant counts. No unrecorded grid/random sweeps. Append hypothesis, source SHA256, symbols, raw screen metrics, frozen null result if run, eligibility gates, economics, mechanism, and variants to `experiments.jsonl`. Commit only `strategy.py`, `experiments.jsonl`, and mechanism notes. Push then submit self-reported development result. Reproduce another candidate before adoption.

## Sealed validation
Freeze up to three distinct SHA256 finalists with eligible development evidence. Submit:

```bash
python3 /usr/local/bin/v32-validate --strategy strategy.py --symbols MNQ,MCL
```

Receipt exposes status, SHA, quota only. No validation metrics, errors, traces, or timing. Accepted failure consumes quota. Do not change candidate or identity to evade caps. Validator reruns 200 null seeds and records eligibility for owner review only.

After budget exhaustion: save mechanism notes, submit frozen finalists only, post completion, create `.hive/research-complete`, exit.
