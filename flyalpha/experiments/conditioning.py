"""A tiny conditioning experiment for the fly-inspired learning loop."""

from __future__ import annotations

from dataclasses import dataclass

from flyalpha.actions import TradingAction, action_from_population
from flyalpha.environment import execute_position, reward_from_execution
from flyalpha.mushroom_body import DopamineSignal, KCToMBONPlasticity, KenyonActivity
from flyalpha.senses import MarketCandle, SpikeEncoder, encode_market_features


@dataclass(frozen=True)
class ConditioningResult:
    """Summary from a toy learning run."""

    rewards: tuple[float, ...]
    actions: tuple[TradingAction, ...]
    learned_weights: dict[tuple[str, str], float]

    @property
    def cumulative_reward(self) -> float:
        return sum(self.rewards)


def _kenyon_from_market(previous: MarketCandle, current: MarketCandle) -> KenyonActivity:
    features = encode_market_features(previous, current)
    sensory_spikes = SpikeEncoder(sensitivity=0.005).encode(features)
    active_cells = {
        f"kc_{name.removeprefix('sens_')}"
        for tick in sensory_spikes
        for name in tick
    }
    return KenyonActivity(active_cells=frozenset(active_cells))


def run_conditioning_demo(episodes: int = 12) -> ConditioningResult:
    """Condition a fly-like memory to favor LONG in a rising toy market."""

    plasticity = KCToMBONPlasticity(learning_rate=0.1, trace_decay=0.6)
    previous = MarketCandle(open=100.0, high=101.0, low=99.0, close=100.0, volume=1000.0)
    rewards: list[float] = []
    actions: list[TradingAction] = []
    expected_reward = 0.0

    for episode in range(episodes):
        current = MarketCandle(
            open=100.0 + episode,
            high=102.0 + episode,
            low=99.5 + episode,
            close=101.0 + episode,
            volume=1000.0 + episode * 10.0,
        )
        kenyon_activity = _kenyon_from_market(previous, current)
        readout = plasticity.readout(kenyon_activity)
        population = readout.dominant_population
        action = action_from_population(population)
        plasticity.activate(kenyon_activity, population)

        execution = execute_position(action, previous, current)
        reward = reward_from_execution(execution)
        rpe = reward - expected_reward
        expected_reward += 0.2 * rpe
        plasticity.apply_dopamine(DopamineSignal.from_prediction_error(rpe))

        rewards.append(reward)
        actions.append(action)
        previous = current

    return ConditioningResult(
        rewards=tuple(rewards),
        actions=tuple(actions),
        learned_weights=dict(plasticity.weights),
    )

