"""Dopamine-gated KC-to-MBON plasticity."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .dopamine import DopamineSignal
from .kenyon import KenyonActivity
from .mbon import MBONReadout


@dataclass
class KCToMBONPlasticity:
    """Three-factor learning rule over eligible KC-to-MBON synapses."""

    learning_rate: float = 0.05
    trace_decay: float = 0.8
    min_weight: float = -2.0
    max_weight: float = 2.0
    weights: dict[tuple[str, str], float] = field(default_factory=dict)
    eligibility: dict[tuple[str, str], float] = field(default_factory=lambda: defaultdict(float))
    mbons: tuple[str, ...] = ("approach", "avoidance", "hold")

    def activate(self, kenyon_activity: KenyonActivity, chosen_mbon: str) -> None:
        if chosen_mbon not in self.mbons:
            raise ValueError(f"unknown MBON population: {chosen_mbon}")
        self._decay_traces()
        for kc_id in kenyon_activity.active_cells:
            self.eligibility[(kc_id, chosen_mbon)] += 1.0

    def readout(self, kenyon_activity: KenyonActivity) -> MBONReadout:
        totals = dict.fromkeys(self.mbons, 0.0)
        for kc_id in kenyon_activity.active_cells:
            for mbon in self.mbons:
                totals[mbon] += self.weights.get((kc_id, mbon), 0.0)
        return MBONReadout(
            approach=totals["approach"],
            avoidance=totals["avoidance"],
            hold=totals["hold"],
        )

    def apply_dopamine(self, signal: DopamineSignal) -> None:
        for synapse, trace in list(self.eligibility.items()):
            current = self.weights.get(synapse, 0.0)
            updated = current + self.learning_rate * trace * signal.signed_value
            self.weights[synapse] = min(self.max_weight, max(self.min_weight, updated))
        self._decay_traces()

    def reset_memory(self) -> None:
        self.weights.clear()
        self.eligibility.clear()

    def _decay_traces(self) -> None:
        for synapse, trace in list(self.eligibility.items()):
            decayed = trace * self.trace_decay
            if decayed < 1e-6:
                del self.eligibility[synapse]
            else:
                self.eligibility[synapse] = decayed

