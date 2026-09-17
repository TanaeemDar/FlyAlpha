# FlyAlpha Run Findings

Generated from completed local reports on 2026-09-17.

## Report Directories

```text
runs/20260917_103758_stats
runs/20260917_104131_tune
runs/20260917_115337_walk_forward
runs/20260917_121942_ablation
runs/20260917_122040_credit
```

The tested CSV was:

```text
/home/rev/tanaeem/NY-Open-Momentum/data/bybit/BTCUSDT_linear_M5_202109110520_202609111115.csv
```

## Full-File Stats

Using the selected tuned configuration on the full BTCUSDT file:

```text
Final equity:      10609.54
Cumulative reward: 609.54
Profit factor:     1.3261
Max drawdown:      313.16
Active trades:     2996
Active win rate:   44.63%
```

Interpretation: the selected configuration is profitable on the full file, with
PF above 1.0 and controlled drawdown relative to the 10,000 starting equity.

## Tuning

Best tuning result on the 50k-candle tuning run:

```text
learning_rate: 0.05
trace_decay:   0.8
risk:          0.0025
stop:          0.02
take profit:   0.04
trend filter:  12-candle aligned

Reward:        4099.38
Profit factor: 1.6908
Max drawdown:  59.97
```

Interpretation: the PF objective found a strong in-sample configuration.

## Walk-Forward Validation

Walk-forward was the most important robustness check.

```text
Windows:                 32
PF > 1 windows:          8 / 32
PF > 1 percentage:       25%
Total reward:            8712.79
Average window reward:   272.27
Median PF:               0.6821
Average PF:              0.7924
Best PF:                 1.8205, window 1
Worst PF:                0.2409, window 31
Worst MDD:               690.68, window 10
Positive reward windows: 8 / 32
```

Interpretation: total walk-forward reward is positive, but robustness is weak.
A few large winning windows carry the result. Median PF below 1.0 means the
current system is regime-dependent and not yet reliable.

## Ablations

```text
full:
  reward: 832.90
  PF:     1.6153
  MDD:    89.86

dopamine_disabled:
  reward: -2369.21
  PF:     0.8498
  MDD:    2434.68

plasticity_frozen:
  reward: -2369.21
  PF:     0.8498
  MDD:    2434.68

random_reward:
  reward: -89.86
  PF:     0.6220
  MDD:    93.28

reward_delay_12:
  reward: -34.80
  PF:     0.6652
  MDD:    48.15
```

Interpretation: dopamine-modulated plasticity matters in the current system.
Disabling dopamine, freezing plasticity, or randomizing reward degrades the
result substantially.

`degree_preserving_random` is scaffolded but not yet executable because a real
MaleCNS graph loader is not connected to the active simulation path.

## Credit Assignment

Best notable credit-assignment rows:

```text
delay=0, trace=0.8:
  reward: 832.90
  PF:     1.6153
  MDD:    89.86

delay=1, trace=0.8:
  reward: 1689.97
  PF:     1.2312
  MDD:    169.94

delay=3, trace=0.8:
  reward: 1202.70
  PF:     1.1290
  MDD:    560.73
```

Interpretation: the credit-assignment bridge is highly influential. Small
reward delays can still work, but longer delays and poorly matched trace decay
often degrade PF and increase drawdown.

## Bottom Line

Promising:

- full-file PF is above 1.0;
- ablations support the importance of dopamine/plasticity;
- some delayed-reward configurations remain profitable.

Not yet robust:

- only 8 of 32 walk-forward windows have PF above 1.0;
- median walk-forward PF is 0.6821;
- results are regime-dependent.

## Next Target

Improve walk-forward consistency before claiming robustness.

Target:

```text
PF > 1 on at least 50-60% of walk-forward windows
median walk-forward PF > 1
lower worst-window MDD
```

Recommended next engineering direction:

- add richer deterministic regime filters;
- tune for median walk-forward PF rather than single-window PF;
- add full MaleCNS graph loading before claiming real fly-connectome topology;
- make degree-preserving randomized topology executable once the graph loader is connected.

