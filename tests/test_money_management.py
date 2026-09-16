from flyalpha.actions import TradingAction
from flyalpha.environment import MoneyManagementConfig, execute_position, plan_position, reward_from_execution
from flyalpha.senses import MarketCandle


def test_position_plan_caps_risk_and_notional():
    candle = MarketCandle(open=100, high=101, low=99, close=100, volume=1000)
    config = MoneyManagementConfig(
        initial_equity=10_000,
        risk_per_trade=0.01,
        stop_loss_pct=0.01,
        max_position_fraction=0.5,
    )

    plan = plan_position(TradingAction.LONG, candle, equity=10_000, config=config)

    assert plan.quantity == 50
    assert plan.notional == 5000
    assert plan.stop_price == 99
    assert plan.take_profit_price == 102


def test_execution_respects_long_stop_loss():
    entry = MarketCandle(open=100, high=101, low=99, close=100, volume=1000)
    exit_ = MarketCandle(open=100, high=101, low=98, close=100.5, volume=1000)

    execution = execute_position(
        TradingAction.LONG,
        entry,
        exit_,
        quantity=10,
        stop_price=99,
    )

    assert execution.exit_reason == "stop"
    assert reward_from_execution(execution) < 0

