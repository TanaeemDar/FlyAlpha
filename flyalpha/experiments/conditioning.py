"""A tiny conditioning experiment for the fly-inspired learning loop."""

from __future__ import annotations

from dataclasses import dataclass

from flyalpha.actions import TradingAction
from flyalpha.environment import MoneyManagementConfig, execute_position, plan_position, reward_from_execution
from flyalpha.mushroom_body import DopamineSignal, KCToMBONPlasticity, KenyonActivity
from flyalpha.senses import MarketCandle, SpikeEncoder, encode_market_features
from .strategy import StrategyFilterConfig, action_from_readout


@dataclass(frozen=True)
class ConditioningResult:
    """Summary from a toy learning run."""

    rewards: tuple[float, ...]
    actions: tuple[TradingAction, ...]
    learned_weights: dict[tuple[str, str], float]
    equity_curve: tuple[float, ...] = ()
    quantities: tuple[float, ...] = ()

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


def run_conditioning_demo(
    episodes: int = 12,
    learning_rate: float = 0.1,
    trace_decay: float = 0.6,
    money_management: MoneyManagementConfig | None = None,
    strategy_filter: StrategyFilterConfig | None = None,
) -> ConditioningResult:
    """Condition a fly-like memory to favor LONG in a rising toy market."""

    plasticity = KCToMBONPlasticity(learning_rate=learning_rate, trace_decay=trace_decay)
    previous = MarketCandle(open=100.0, high=101.0, low=99.0, close=100.0, volume=1000.0)
    rewards: list[float] = []
    actions: list[TradingAction] = []
    equity_curve: list[float] = []
    quantities: list[float] = []
    equity = money_management.initial_equity if money_management else 0.0
    expected_reward = 0.0
    history = [previous]

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
        action = action_from_readout(readout, previous, current, history, strategy_filter)
        plasticity.activate(kenyon_activity, population)

        if money_management:
            plan = plan_position(action, previous, equity, money_management)
            execution = execute_position(
                plan.action,
                previous,
                current,
                cost_bps=money_management.cost_bps,
                quantity=plan.quantity,
                stop_price=plan.stop_price,
                take_profit_price=plan.take_profit_price,
                breakeven_trigger_pct=money_management.breakeven_trigger_pct,
                trailing_stop_pct=money_management.trailing_stop_pct,
            )
            action = plan.action
        else:
            execution = execute_position(action, previous, current)
        reward = reward_from_execution(execution)
        if money_management:
            equity += reward
            equity_curve.append(equity)
            quantities.append(execution.quantity)
        rpe = reward - expected_reward
        expected_reward += 0.2 * rpe
        plasticity.apply_dopamine(DopamineSignal.from_prediction_error(rpe))

        rewards.append(reward)
        actions.append(action)
        previous = current
        history.append(current)

    return ConditioningResult(
        rewards=tuple(rewards),
        actions=tuple(actions),
        learned_weights=dict(plasticity.weights),
        equity_curve=tuple(equity_curve),
        quantities=tuple(quantities),
    )


def run_conditioning_on_candles(
    candles: list[MarketCandle],
    learning_rate: float = 0.1,
    trace_decay: float = 0.6,
    money_management: MoneyManagementConfig | None = None,
    strategy_filter: StrategyFilterConfig | None = None,
) -> ConditioningResult:
    """Run the same fly-learning loop over existing candle data."""

    if len(candles) < 2:
        raise ValueError("at least two candles are required")

    plasticity = KCToMBONPlasticity(learning_rate=learning_rate, trace_decay=trace_decay)
    rewards: list[float] = []
    actions: list[TradingAction] = []
    equity_curve: list[float] = []
    quantities: list[float] = []
    equity = money_management.initial_equity if money_management else 0.0
    expected_reward = 0.0
    history = [candles[0]]

    for previous, current in zip(candles, candles[1:]):
        kenyon_activity = _kenyon_from_market(previous, current)
        readout = plasticity.readout(kenyon_activity)
        population = readout.dominant_population
        action = action_from_readout(readout, previous, current, history, strategy_filter)
        plasticity.activate(kenyon_activity, population)

        if money_management:
            plan = plan_position(action, previous, equity, money_management)
            execution = execute_position(
                plan.action,
                previous,
                current,
                cost_bps=money_management.cost_bps,
                quantity=plan.quantity,
                stop_price=plan.stop_price,
                take_profit_price=plan.take_profit_price,
                breakeven_trigger_pct=money_management.breakeven_trigger_pct,
                trailing_stop_pct=money_management.trailing_stop_pct,
            )
            action = plan.action
        else:
            execution = execute_position(action, previous, current)
        reward = reward_from_execution(execution)
        if money_management:
            equity += reward
            equity_curve.append(equity)
            quantities.append(execution.quantity)
        rpe = reward - expected_reward
        expected_reward += 0.2 * rpe
        plasticity.apply_dopamine(DopamineSignal.from_prediction_error(rpe))

        rewards.append(reward)
        actions.append(action)
        history.append(current)

    return ConditioningResult(
        rewards=tuple(rewards),
        actions=tuple(actions),
        learned_weights=dict(plasticity.weights),
        equity_curve=tuple(equity_curve),
        quantities=tuple(quantities),
    )
