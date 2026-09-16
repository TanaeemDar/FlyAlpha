from flyalpha.brain import LIFNeuron, NeuralGraph, WeightedSynapse


def test_spike_propagates_across_graph():
    graph = NeuralGraph(
        neurons=[
            LIFNeuron("sens_return_pos"),
            LIFNeuron("kc_return_pos", threshold=0.5),
        ],
        synapses=[WeightedSynapse("sens_return_pos", "kc_return_pos", 1.0)],
    )

    result = graph.run([{"sens_return_pos"}, set()], ticks=2)

    assert "kc_return_pos" in result.spikes_by_tick[1]

