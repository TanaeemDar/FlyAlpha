# FlyAlpha Latest Run Findings

Generated from completed local reports checked on 2026-09-18.

These reports were produced from the local BTCUSDT 5-minute CSV:

```text
/home/rev/tanaeem/NY-Open-Momentum/data/bybit/BTCUSDT_linear_M5_202109110520_202609111115.csv
```

## Report Directories

```text
runs/20260917_103758_stats
runs/20260917_104131_tune
runs/20260917_132354_walk_forward
runs/20260917_122040_credit
runs/20260918_145829_ablation
```

The newest files checked were:

```text
runs/20260918_145829_ablation/ablations.csv
runs/20260918_145829_ablation/summary.json
runs/20260917_132354_walk_forward/walk_forward.csv
runs/20260917_132354_walk_forward/summary.json
```

## Baseline Full-File Stats

Using the selected configuration on the full BTCUSDT file:

```text
Final equity:      10609.54
Cumulative reward: 609.54
Profit factor:     1.3261
Max drawdown:      313.16
Active trades:     2996
Active win rate:   44.63%
Learned weights:   24
```

Interpretation: the full-file run is profitable, with PF above 1.0. This is a
useful sanity check, but it is not enough by itself because a single full-period
backtest can hide regime dependence.

## Best Tuning Result

Best PF-focused tuning result from the 50k-candle tuning run:

```text
learning_rate:     0.05
trace_decay:       0.8
risk_per_trade:    0.0025
stop_loss_pct:     0.02
take_profit_pct:   0.04
trend_filter:      12-candle aligned

Cumulative reward: 4099.38
Profit factor:     1.6908
Max drawdown:      59.97
```

The best reward result was larger, but had lower PF:

```text
learning_rate:     0.02
trace_decay:       0.8
risk_per_trade:    0.0025
stop_loss_pct:     0.01
take_profit_pct:   0.04
trend_filter:      12-candle aligned

Cumulative reward: 11912.98
Profit factor:     1.5483
Max drawdown:      189.33
```

Interpretation: tuning can find profitable parameter sets, but selecting by
in-sample PF or reward is still vulnerable to overfitting. The real check is
walk-forward validation.

## Latest Walk-Forward Validation

Latest walk-forward report:

```text
runs/20260917_132354_walk_forward/walk_forward.csv
```

Summary:

```text
Windows:                 32
PF > 1 windows:          9 / 32
Positive reward windows: 9 / 32
Total reward:            5658.30
Average window reward:   176.82
Median PF:               0.6169
Average PF:              0.7604
Max MDD:                 470.07
Average MDD:             47.72
Total active trades:     30790
```

Best PF window:

```text
Window:       1
PF:           1.8205
Reward:       1645.08
MDD:          44.10
Active trades: 2466
```

Best reward window:

```text
Window:       19
PF:           1.2099
Reward:       2076.92
MDD:          470.07
```

Worst PF window:

```text
Window:       31
PF:           0.2411
Reward:       -45.38
MDD:          47.93
```

Interpretation: this is the key weakness. The system can produce strong
profitable windows, but only 9 of 32 walk-forward windows have PF above 1.0.
Median PF remains below 1.0, so the current configuration is not robust enough
for public performance claims or live trading.

## Walk-Forward Comparison

The newer walk-forward run improved drawdown but did not improve median PF:

| Report | Windows | PF > 1 | Median PF | Average PF | Total reward | Max MDD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `20260917_115337_walk_forward` | 32 | 8 | 0.6821 | 0.7924 | 8712.79 | 690.68 |
| `20260917_132354_walk_forward` | 32 | 9 | 0.6169 | 0.7604 | 5658.30 | 470.07 |

Interpretation: the newer run has one more profitable window and lower worst
drawdown, but total reward, median PF, and average PF are lower. This is a
mixed result, not a clean robustness improvement.

## Latest Ablation Results

Latest ablation report:

```text
runs/20260918_145829_ablation/ablations.csv
```

| Control | PF | Reward | MDD | Active trades | Win rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| full | 1.5625 | 797.68 | 125.32 | 1932 | 47.31% |
| dopamine_disabled | 0.8552 | -4097.41 | 4114.41 | 49908 | 44.00% |
| plasticity_frozen | 0.8552 | -4097.41 | 4114.41 | 49908 | 44.00% |
| random_reward | 0.5636 | -152.35 | 155.05 | 688 | 38.52% |
| reward_delay_12 | 0.5619 | -127.46 | 141.02 | 631 | 38.99% |

Interpretation: this is the strongest scientific signal in the current reports.
The full dopamine-plasticity loop is profitable, while disabling dopamine,
freezing plasticity, randomizing reward, or delaying reward substantially
degrades PF. That supports the claim that the current learning loop matters.

It does not yet prove that the biological topology itself is responsible. The
degree-preserving randomized-connectome control is scaffolded, but needs a real
MaleCNS graph loader connected to the active simulation path before it can be a
decisive topology ablation.

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

Interpretation: the credit-assignment bridge is highly influential. Small reward
delays can remain profitable, but longer delays and poorly matched trace decay
can quickly degrade PF or increase drawdown.

## Bottom Line

Promising:

- full-file PF is above 1.0;
- tuned configurations can reach PF around 1.6 to 1.7;
- ablations strongly support dopamine-gated plasticity as useful;
- delayed reward can work when trace decay is matched well.

Not yet robust:

- latest walk-forward PF is above 1.0 in only 9 of 32 windows;
- median walk-forward PF is 0.6169;
- profitable behavior is regime-dependent;
- full MaleCNS topology is not yet in the live simulation path.

## Next Target

Improve walk-forward consistency before making any stronger claim.

Target:

```text
PF > 1 on at least 50-60% of walk-forward windows
median walk-forward PF > 1
lower worst-window MDD
```

Recommended next engineering direction:

- tune against walk-forward median PF, not only in-sample PF;
- add deterministic regime filters for volatility and trend quality;
- expand ablations to include degree-preserving topology randomization;
- connect the real MaleCNS graph loader before claiming fly-connectome topology;
- keep live-trading support behind paper mode until walk-forward robustness improves.
