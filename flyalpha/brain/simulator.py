"""Simple synchronous spike propagation over a directed neural graph."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from .lif import LIFNeuron
from .synapse import WeightedSynapse


@dataclass(frozen=True)
class SimulationResult:
    """Spikes emitted during a simulation window."""

    spikes_by_tick: list[set[str]]

    @property
    def spike_counts(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for spikes in self.spikes_by_tick:
            for neuron_id in spikes:
                counts[neuron_id] += 1
        return dict(counts)


class NeuralGraph:
    """A deterministic LIF graph with external spike injection."""

    def __init__(self, neurons: Iterable[LIFNeuron], synapses: Iterable[WeightedSynapse]):
        self.neurons = {neuron.neuron_id: neuron for neuron in neurons}
        self.outgoing: dict[str, list[WeightedSynapse]] = defaultdict(list)
        for synapse in synapses:
            if synapse.pre_neuron_id not in self.neurons:
                raise ValueError(f"unknown pre neuron: {synapse.pre_neuron_id}")
            if synapse.post_neuron_id not in self.neurons:
                raise ValueError(f"unknown post neuron: {synapse.post_neuron_id}")
            self.outgoing[synapse.pre_neuron_id].append(synapse)

    def reset(self) -> None:
        for neuron in self.neurons.values():
            neuron.reset()

    def run(self, external_spikes: Iterable[set[str]], ticks: int | None = None) -> SimulationResult:
        """Run the graph with optional externally injected spikes per tick."""

        schedule = list(external_spikes)
        total_ticks = ticks if ticks is not None else len(schedule)
        pending: dict[str, float] = defaultdict(float)
        spikes_by_tick: list[set[str]] = []

        for tick in range(total_ticks):
            emitted = set(schedule[tick]) if tick < len(schedule) else set()
            for neuron_id in emitted:
                if neuron_id not in self.neurons:
                    raise ValueError(f"unknown external neuron: {neuron_id}")

            for neuron_id, neuron in self.neurons.items():
                if neuron_id in emitted:
                    continue
                if neuron.step(pending.pop(neuron_id, 0.0)):
                    emitted.add(neuron_id)

            next_pending: dict[str, float] = defaultdict(float)
            for pre_neuron_id in emitted:
                for synapse in self.outgoing.get(pre_neuron_id, []):
                    next_pending[synapse.post_neuron_id] += synapse.weight
            pending = next_pending
            spikes_by_tick.append(emitted)

        return SimulationResult(spikes_by_tick=spikes_by_tick)

