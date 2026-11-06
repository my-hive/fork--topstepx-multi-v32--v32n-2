# v32n-2 development mechanism notes

## Outcome

15 recorded experiments used; 15 left unused. No candidate passed the development economic gates. No frozen finalist, 200-seed null run, or sealed validation submission. Screen score zero is expected without a null and is not evidence of failure by itself; the negative PnL/yearly gates are the rejection reasons.

All 49 supplied development markets were included in fixed broad diagnostics. Account simulations used manageable one- or four-market subsets. Full-size and reduced contracts on the same underlying were not treated as independent evidence.

## Ranked non-eligible candidates

These are research records, not finalists or claims of deployable profitability.

1. Experiment 6, source `c8a95e81a55f9f7c8d632657d39870ff7d79597a7513eb5f8893707e3287b68f`, RB overnight-gap fade: stressed PnL **+$17,377.20**, but only **3/14 positive years**. Entry risk max $299.61 and entry diversity passed. Positive total was concentrated in 2017, 2020, and 2022. Rejected for yearly economics; raw account score remained zero.
2. Experiment 15, source `21fbba967f149c09485382dc09069d0dd7901f30adfc394c1a02f5d66b0914e7`, MYM overnight-gap fade: stressed PnL **-$317.00**, 3/5 positive years. Rejected.
3. Experiment 11, source `70091e1672471600b3b185c90da6cc0825dfe4231b56ed96a8613cbda93ac391`, CL large-opening-move fade: stressed PnL **-$1,515.00**, 5/14 positive years. Rejected.

Experiment 14, source `f1abb455895bef89d26053a2be2baddcdff44cf7d0e2c7e76b6fdf5d4530892e`, delayed RB low-volume fade, improved to **-$5,049.00** with 7/14 positive years but remained ineligible.

## Mechanism findings

- Failed opening-range retakes lost on both fade and continuation sides after next-open execution and stressed costs. A causal stop at 1.5 times lagged 20-bar ATR with an opening-midpoint target did not rescue the fade; M2K experiment 9 lost $3,507.25 with every year negative.
- Unconditional opening-move, overnight-gap, first-30-minute, cross-sectional equity, and low-volume reversion diagnostics did not produce stable all-year positive economics.
- Large-move filters produced sparse, regime-dependent energy profits in simplified diagnostics. Trusted CL execution did not reproduce the diagnostic gain. Raising the threshold to 1.0 lagged daily ATR left only four CL entries and lost $1,810.
- Micro-equity opening-return cross-sectional reversion lost $14,306 in its fixed diagnostic, with 0/5 positive years. The trusted attempt timed out because of inefficient implementation; the diagnostic gave no reason to optimize it further.
- Stressed round-trip costs and realistic gap/data-end handling erased small gross anomalies. Requiring later bars in diagnostics can silently drop losing sessions; this selection bias was identified and rejected.

## Causality and execution lessons

- Entry risk arrays must be finite even during warmup, while entries remain disabled until enough history exists.
- Signals must not require a future exit row before emitting an earlier target; experiment 4 failed the prefix check for this reason.
- Evaluator gap/roll handling flattens at the prior close. Persistent targets can reenter after gaps unless explicitly blocked. Experiments 5 and 6 measured this effect.
- Session `ct_sec` wraps across midnight. All diagnostics used boolean time windows rather than binary search on unfiltered session arrays.
- Prior session references and rolling history must be built forward only. No calendar/date selection, full-sample normalization, future shifts, fractional sizing, or hidden parameter sweeps were used.

## Decision

No source SHA was promoted to sealed validation because none had eligible development evidence. Development scores were not interpreted as deployability evidence.
