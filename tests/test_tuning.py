from flyalpha.experiments.tuning import format_tuning_report, format_validation_report, run_train_test_validation, run_tuning_grid
from flyalpha.senses import MarketCandle


def test_tuning_grid_returns_ranked_trials():
    trials = run_tuning_grid(
        episodes=3,
        learning_rates=(0.05, 0.1),
        trace_decays=(0.6,),
    )

    assert len(trials) == 2
    assert trials[0].cumulative_reward >= trials[1].cumulative_reward
    assert "FlyAlpha tuning report" in format_tuning_report(trials)


def test_train_test_validation_reports_holdout():
    candles = [
        MarketCandle(open=100 + index, high=102 + index, low=99 + index, close=101 + index, volume=1000)
        for index in range(8)
    ]

    result = run_train_test_validation(
        candles,
        learning_rates=(0.05,),
        trace_decays=(0.6,),
    )

    assert result.train_candles >= 2
    assert result.test_candles >= 2
    assert "Evaluated on test" in format_validation_report(result)
