"""Sparse Kenyon-cell activity representation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KenyonActivity:
    """Recently active Kenyon cells."""

    active_cells: frozenset[str]

    @classmethod
    def sparsify(cls, spike_counts: dict[str, int], prefix: str = "kc", top_k: int = 4) -> "KenyonActivity":
        ranked = sorted(
            ((neuron_id, count) for neuron_id, count in spike_counts.items() if neuron_id.startswith(prefix)),
            key=lambda item: (-item[1], item[0]),
        )
        return cls(active_cells=frozenset(neuron_id for neuron_id, _ in ranked[:top_k]))

