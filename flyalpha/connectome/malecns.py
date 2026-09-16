"""MaleCNS v1.0 metadata and minimal graph records.

FlyAlpha does not bundle the MaleCNS dataset. These records define the shape
used by local experiments and make attribution explicit for downstream loaders.
"""

from __future__ import annotations

from dataclasses import dataclass


MALECNS_PROVENANCE = {
    "dataset": "MaleCNS v1.0",
    "organism": "Drosophila melanogaster, adult male",
    "scope": "central brain, optic lobes, and ventral nerve cord",
    "license": "CC-BY",
    "released": "2026-06-08",
    "publication": "Cell, 2026-09-03",
    "source": "https://www.janelia.org/project-team/flyem/male-cns-connectome",
}


@dataclass(frozen=True)
class ConnectomeNeuron:
    """A biologically named node in the executable graph."""

    neuron_id: str
    neuron_type: str
    neurotransmitter: str = "unknown"
    brain_region: str = "unknown"


@dataclass(frozen=True)
class SynapseEdge:
    """Directed synaptic edge derived from connectome connectivity."""

    pre_neuron_id: str
    post_neuron_id: str
    synapse_count: int

    @property
    def structural_weight(self) -> float:
        """Log-scaled synapse count for stable toy simulations."""

        if self.synapse_count <= 0:
            return 0.0
        return 1.0 + min(self.synapse_count, 100) / 100.0
