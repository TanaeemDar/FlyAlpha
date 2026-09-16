from flyalpha.actions import TradingAction, action_from_population
from flyalpha.environment import execute_position, reward_from_execution
from flyalpha.experiments import run_conditioning_demo
from flyalpha.senses import MarketCandle, SpikeEncoder, encode_market_features
from flyalpha.visualization import sparkline


def test_market_encoding_and_reward_smoke():
    previous = MarketCandle(open=100, high=101, low=99, close=100, volume=1000)
    current = MarketCandle(open=100, high=103, low=99, close=102, volume=1100)

    features = encode_market_features(previous, current)
    spikes = SpikeEncoder().encode(features)
    action = action_from_population("approach")
    reward = reward_from_execution(execute_position(action, previous, current))

    assert "sens_return_pos" in spikes[0]
    assert action is TradingAction.LONG
    assert reward > 0


def test_conditioning_demo_learns_weights():
    result = run_conditioning_demo(episodes=6)

    assert len(result.actions) == 6
    assert result.learned_weights
    assert sparkline(result.rewards)


def test_sparkline_is_bounded_for_large_inputs():
    assert len(sparkline(tuple(range(1000)), width=40)) == 40
