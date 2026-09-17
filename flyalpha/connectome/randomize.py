"""Degree-preserving randomization helpers for future connectome-backed graphs."""

from __future__ import annotations

from random import Random

from flyalpha.brain import WeightedSynapse


def degree_preserving_rewire(
    synapses: list[WeightedSynapse],
    swaps: int,
    seed: int = 7,
) -> list[WeightedSynapse]:
    """Randomize directed edges while preserving in/out degree and weights."""

    rng = Random(seed)
    rewired = list(synapses)
    seen = {(synapse.pre_neuron_id, synapse.post_neuron_id) for synapse in rewired}
    if len(rewired) < 2:
        return rewired

    for _ in range(swaps):
        first_index, second_index = rng.sample(range(len(rewired)), 2)
        first = rewired[first_index]
        second = rewired[second_index]
        if first.pre_neuron_id == second.pre_neuron_id or first.post_neuron_id == second.post_neuron_id:
            continue
        candidate_a = (first.pre_neuron_id, second.post_neuron_id)
        candidate_b = (second.pre_neuron_id, first.post_neuron_id)
        if candidate_a in seen or candidate_b in seen:
            continue
        seen.remove((first.pre_neuron_id, first.post_neuron_id))
        seen.remove((second.pre_neuron_id, second.post_neuron_id))
        seen.add(candidate_a)
        seen.add(candidate_b)
        rewired[first_index] = WeightedSynapse(candidate_a[0], candidate_a[1], first.weight)
        rewired[second_index] = WeightedSynapse(candidate_b[0], candidate_b[1], second.weight)
    return rewired

