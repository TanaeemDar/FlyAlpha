from flyalpha.experiments.metrics import calculate_reward_metrics


def test_calculate_reward_metrics():
    metrics = calculate_reward_metrics((2.0, -1.0, 3.0, -4.0, 1.0))

    assert metrics.gross_profit == 6.0
    assert metrics.gross_loss == 5.0
    assert metrics.profit_factor == 1.2
    assert metrics.max_drawdown == 4.0

