# FlyAlpha

[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-2E7D32)](LICENSE)
[![Status](https://img.shields.io/badge/status-research%20scaffold-6A4C93)](#roadmap)

FlyAlpha is an open-source research scaffold for a financial-learning agent
whose learning and decision loop is constrained by fruit-fly nervous-system
ideas rather than conventional machine-learning predictors.

The core rule is simple:

> No transformer, no policy network, no boosted-tree predictor, no
> backpropagation decision model. Market inputs are deterministic; neural
> decisions come from fly-inspired spiking dynamics; learning is localized to a
> mushroom-body-inspired dopamine plasticity layer.

```text
        MARKET CANDLES
  OHLCV / return / range / volume
               |
               v
   deterministic sensory encoding
               |
               v
   sensory spikes into fly channels
               |
               v
+-----------------------------------+
|        FLY-INSPIRED CNS           |
|                                   |
|  LIF neurons -> synaptic graph    |
|          |                        |
|          v                        |
|  sparse Kenyon-cell activity      |
|          |                        |
|          v                        |
|  KC -> MBON dopamine plasticity   |
|          |                        |
|          v                        |
|  approach / avoidance / hold      |
+-----------------------------------+
               |
               v
        LONG / SHORT / FLAT
               |
               v
     reward prediction error
               |
               v
        PAM / PPL1 dopamine
```

## Why This Exists

MaleCNS v1.0 is a public adult male *Drosophila melanogaster* central nervous
system connectome covering the brain, optic lobes, and ventral nerve cord. The
project page lists the v1.0 release on 2026-06-08, the paper publication on
2026-09-03, and describes the dataset as licensed under CC-BY.

FlyAlpha asks a narrow, testable question:

Can a fly-inspired circuit adapt through dopamine-gated mushroom-body plasticity
in a market-like environment before we ever ask whether it can trade well?

## Fly Brain Activities We Use

| Fly activity | FlyAlpha role |
| --- | --- |
| Sensory transduction | Converts deterministic market features into spike channels |
| Synaptic propagation | Runs activity through an executable directed neural graph |
| Kenyon-cell sparsity | Compresses active sensory patterns into sparse memory traces |
| MBON output | Produces approach, avoidance, and hold population activity |
| PAM-like dopamine | Reinforces eligible synapses after better-than-expected outcomes |
| PPL1-like dopamine | Penalizes eligible synapses after worse-than-expected outcomes |
| Eligibility traces | Keeps recently active KC-to-MBON synapses available for delayed reinforcement |
| Three-factor plasticity | Updates weights from activity, eligibility, and dopamine together |

The LONG / SHORT / FLAT interface is an engineering bridge, not a biological
claim about native fly behavior.

## Repository Map

```text
flyalpha/
  connectome/       MaleCNS provenance and graph records
  brain/            leaky integrate-and-fire neuron simulation
  mushroom_body/    Kenyon activity, MBON readout, PAM/PPL1 dopamine, plasticity
  senses/           deterministic market feature and spike encoders
  actions/          output-population to trading-action mapping
  environment/      execution and reward helpers
  experiments/      toy conditioning experiment
  visualization/    dependency-free learning traces
docs/               biology, assumptions, and architecture notes
tests/              smoke tests for the learning loop
```

## Quick Start

```bash
python -m pytest -q
```

Use the centralized runner for local stats:

```bash
python -m flyalpha.runner stats --episodes 12
```

Tune the current mushroom-body plasticity parameters:

```bash
python -m flyalpha.runner tune --episodes 24 --limit 10
```

Run stats on an existing OHLCV CSV:

```bash
python -m flyalpha.runner stats --csv path/to/candles.csv
```

Tune against an existing CSV:

```bash
python -m flyalpha.runner tune \
  --csv path/to/candles.csv \
  --learning-rates 0.01,0.05,0.1,0.2 \
  --trace-decays 0.4,0.6,0.8 \
  --limit 10
```

CSV files need these columns:

```text
open,high,low,close,volume
```

Column names are case-insensitive, and extra columns such as `timestamp` or
`symbol` are ignored.

Run one safe paper-trading tick:

```bash
python -m flyalpha.runner trade --mode paper --symbol BTCUSD --action LONG --quantity 0.1
```

If installed as a package, the same commands are available through:

```bash
flyalpha stats --episodes 12
flyalpha tune --episodes 24
flyalpha trade --mode paper --symbol BTCUSD --action LONG --quantity 0.1
```

## Exchange Connectivity

FlyAlpha separates the fly-learning core from exchange APIs:

```text
flyalpha.runner
    |
    v
trading_loop.py
    |
    v
ExchangeClient protocol
    |
    +-- PaperExchangeClient   local simulated fills
    |
    +-- RestExchangeClient    generic REST scaffold for crypto/forex APIs
```

Live trading is intentionally gated. A live order requires:

- an exchange-specific REST base URL;
- API credentials in environment variables;
- the explicit `--i-understand-live-risk` flag;
- a real adapter aligned to the chosen exchange's official API.

Example shape:

```bash
export FLYALPHA_EXCHANGE_API_KEY="..."
export FLYALPHA_EXCHANGE_API_SECRET="..."

python -m flyalpha.runner trade \
  --mode live \
  --base-url "https://api.your-exchange.example" \
  --symbol BTCUSD \
  --action LONG \
  --quantity 0.01 \
  --i-understand-live-risk
```

The included `RestExchangeClient` expects generic `/ticker`, `/balance`, and
`/order` JSON endpoints. Real exchanges usually differ in paths, signatures,
symbols, order flags, rate limits, and compliance requirements, so production
connectors should subclass or wrap this scaffold for Binance, Coinbase, OANDA,
Alpaca, Interactive Brokers, or any other API-based crypto/forex venue.

## Scientific Controls

Before financial claims, FlyAlpha should compare:

| Control | Purpose |
| --- | --- |
| Full fly + dopamine | Baseline adaptive circuit |
| Dopamine disabled | Tests whether reinforcement matters |
| Plasticity frozen | Tests whether behavior depends on learning |
| Randomized topology | Tests whether biological structure matters |
| Random reward | Tests reward-signal specificity |
| Reset memory | Tests whether learned KC-to-MBON weights explain adaptation |

## Roadmap

| Phase | Deliverable |
| --- | --- |
| 0 | MaleCNS provenance and schema |
| 1 | Executable fly-inspired neural graph |
| 2 | Mushroom-body dopamine plasticity |
| 3 | Conditioning experiment and amnesia control |
| 4 | Deterministic market sensory interface |
| 5 | LONG / SHORT / FLAT neural output mapping |
| 6 | Historical market environment |
| 7 | Ablation studies and randomized controls |
| 8 | Connectome-backed loaders and visual analytics |

## Current Smoke Tests

The included tests verify that:

- spikes propagate through the neural graph;
- dopamine changes only eligible KC-to-MBON synapses;
- deterministic market features produce sensory spikes;
- the conditioning demo creates learned weights.
- the centralized runner accepts stats/tuning/trading commands;
- paper exchange orders are recorded without network access;
- live orders are blocked without explicit confirmation.

## Sources

- MaleCNS project page: https://male-cns.janelia.org/
- Janelia Male CNS overview and downloads: https://www.janelia.org/project-team/flyem/male-cns-connectome
- MaleCNS release notes and CC-BY licensing: https://male-cns.janelia.org/
- Reinforcement-prediction-error-like mushroom-body model: https://www.nature.com/articles/s41586-021-04248-5
- Dopaminergic neuron memory updating in *Drosophila*: https://elifesciences.org/articles/56954
- PAM/PPL dopamine neurons innervating mushroom body: https://www.frontiersin.org/articles/10.3389/neuro.02.005.2009/full

## Disclaimer

FlyAlpha is research software. It is not financial advice, not a trading system,
and not evidence that a fly connectome can produce profitable market behavior.
