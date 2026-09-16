"""Executable fly-inspired neural dynamics."""

from .lif import LIFNeuron
from .simulator import NeuralGraph, SimulationResult
from .synapse import WeightedSynapse

__all__ = ["LIFNeuron", "NeuralGraph", "SimulationResult", "WeightedSynapse"]

