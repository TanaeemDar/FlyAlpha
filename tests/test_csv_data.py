from pathlib import Path

from flyalpha.data import load_candles_csv
from flyalpha.experiments.conditioning import run_conditioning_on_candles
from flyalpha.experiments.stats import summarize_csv
from flyalpha.experiments.tuning import run_tuning_grid


FIXTURE = Path(__file__).parent / "fixtures" / "sample_ohlcv.csv"


def test_load_candles_csv_reads_existing_ohlcv():
    candles = load_candles_csv(FIXTURE)

    assert len(candles) == 5
    assert candles[0].close == 100


def test_csv_conditioning_stats_and_tuning():
    candles = load_candles_csv(FIXTURE)
    result = run_conditioning_on_candles(candles)
    trials = run_tuning_grid(
        learning_rates=(0.05,),
        trace_decays=(0.6,),
        candles=candles,
    )

    assert len(result.rewards) == 4
    assert len(trials) == 1
    assert "sample_ohlcv.csv" in summarize_csv(str(FIXTURE))

