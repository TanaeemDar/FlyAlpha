from flyalpha.actions import TradingAction
from flyalpha.experiments.strategy import StrategyFilterConfig, action_from_readout
from flyalpha.mushroom_body import MBONReadout
from flyalpha.senses import MarketCandle


def test_confidence_filter_suppresses_weak_readout():
    previous = MarketCandle(open=100, high=101, low=99, close=100, volume=1000)
    current = MarketCandle(open=100, high=101, low=99, close=100.1, volume=1000)
    readout = MBONReadout(approach=0.2, avoidance=0.19)

    action = action_from_readout(
        readout,
        previous,
        current,
        [previous],
        StrategyFilterConfig(confidence_threshold=0.05),
    )

    assert action is TradingAction.FLAT


def test_trend_filter_requires_alignment():
    history = [
        MarketCandle(open=102, high=103, low=101, close=102, volume=1000),
        MarketCandle(open=101, high=102, low=100, close=101, volume=1000),
    ]
    current = MarketCandle(open=101, high=102, low=100, close=101.5, volume=1000)

    action = action_from_readout(
        MBONReadout(approach=1.0, avoidance=0.0),
        history[-1],
        current,
        history,
        StrategyFilterConfig(trend_lookback=2, require_trend_alignment=True),
    )

    assert action is TradingAction.FLAT
