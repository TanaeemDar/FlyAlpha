from flyalpha.experiments.stats import summarize


def test_stats_report_contains_key_metrics():
    report = summarize(episodes=4)

    assert "Cumulative reward:" in report
    assert "Win rate:" in report
    assert "Learned weights:" in report

