from flyalpha.brain import WeightedSynapse
from flyalpha.connectome.randomize import degree_preserving_rewire
from flyalpha.experiments.ablation import run_ablation_suite
from flyalpha.experiments.credit import run_credit_assignment_grid
from flyalpha.experiments.reporting import write_rows_csv
from flyalpha.environment import MoneyManagementConfig
from flyalpha.experiments.strategy import StrategyFilterConfig
from flyalpha.senses import MarketCandle


def _candles():
    return [
        MarketCandle(open=100 + index, high=102 + index, low=99 + index, close=101 + index, volume=1000)
        for index in range(8)
    ]


def test_ablation_and_credit_rows_are_created():
    money = MoneyManagementConfig(risk_per_trade=0.001)
    strategy = StrategyFilterConfig()

    ablations = run_ablation_suite(
        _candles(),
        controls=("full", "dopamine_disabled"),
        learning_rate=0.05,
        trace_decay=0.8,
        money_management=money,
        strategy_filter=strategy,
    )
    credit = run_credit_assignment_grid(
        _candles(),
        reward_delays=(0, 2),
        trace_decays=(0.6,),
        learning_rate=0.05,
        money_management=money,
        strategy_filter=strategy,
    )

    assert [row.control for row in ablations] == ["full", "dopamine_disabled"]
    assert len(credit) == 2


def test_degree_preserving_rewire_keeps_degrees_and_weights():
    synapses = [
        WeightedSynapse("a", "x", 1.0),
        WeightedSynapse("b", "y", 2.0),
        WeightedSynapse("c", "z", 3.0),
        WeightedSynapse("d", "w", 4.0),
    ]

    rewired = degree_preserving_rewire(synapses, swaps=20)

    assert sorted(edge.pre_neuron_id for edge in rewired) == sorted(edge.pre_neuron_id for edge in synapses)
    assert sorted(edge.post_neuron_id for edge in rewired) == sorted(edge.post_neuron_id for edge in synapses)
    assert sorted(edge.weight for edge in rewired) == [1.0, 2.0, 3.0, 4.0]


def test_report_writer_accepts_heterogeneous_rows(tmp_path):
    path = tmp_path / "rows.csv"

    write_rows_csv(path, [{"a": 1}, {"a": 2, "b": "note"}])

    assert "b" in path.read_text()

