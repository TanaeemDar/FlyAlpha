"""Synaptic records for executable neural graphs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WeightedSynapse:
    """A directed synapse with an executable weight."""

    pre_neuron_id: str
    post_neuron_id: str
    weight: float

