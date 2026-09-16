# Connectome Provenance

FlyAlpha is designed around MaleCNS v1.0, the adult male *Drosophila melanogaster*
central nervous system connectome. The dataset covers the central brain, optic
lobes, and ventral nerve cord, and Janelia describes the FlyEM Male CNS dataset
as licensed under CC BY.

This repository does not vendor the connectome. Downloaders and loaders should:

- retain original neuron identifiers whenever available;
- preserve neuron type, neurotransmitter, region, and synapse-count metadata;
- document every transformation from biological connectivity to executable
  simulation weights;
- keep artificial market-interface mappings separate from biological claims.

Primary project page:
https://www.janelia.org/project-team/flyem/male-cns-connectome

