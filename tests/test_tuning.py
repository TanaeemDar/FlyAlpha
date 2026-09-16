from flyalpha.experiments.tuning import format_tuning_report, run_tuning_grid


def test_tuning_grid_returns_ranked_trials():
    trials = run_tuning_grid(
        episodes=3,
        learning_rates=(0.05, 0.1),
        trace_decays=(0.6,),
    )

    assert len(trials) == 2
    assert trials[0].cumulative_reward >= trials[1].cumulative_reward
    assert "FlyAlpha tuning report" in format_tuning_report(trials)

