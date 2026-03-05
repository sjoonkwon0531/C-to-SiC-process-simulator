"""Process Ontology — Node/Edge/Property definitions for Petro-C → SiC Digital Twin."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class NodeType(Enum):
    FEEDSTOCK = "feedstock"
    PROCESS = "process"
    INTERMEDIATE = "intermediate"
    PRODUCT = "product"
    UTILITY = "utility"
    WASTE = "waste"


class EdgeType(Enum):
    MATERIAL_FLOW = "material_flow"
    ENERGY_FLOW = "energy_flow"
    INFORMATION = "information"


@dataclass
class ProcessNode:
    """A node in the process ontology graph."""
    id: str
    name: str
    node_type: NodeType
    properties: Dict = field(default_factory=dict)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)


@dataclass
class ProcessEdge:
    """An edge connecting two process nodes."""
    source: str
    target: str
    edge_type: EdgeType
    properties: Dict = field(default_factory=dict)


@dataclass
class ProcessOntology:
    """Full process ontology for Petro-C → SiC."""
    nodes: Dict[str, ProcessNode] = field(default_factory=dict)
    edges: List[ProcessEdge] = field(default_factory=list)

    def add_node(self, node: ProcessNode):
        self.nodes[node.id] = node

    def add_edge(self, edge: ProcessEdge):
        self.edges.append(edge)

    def get_downstream(self, node_id: str) -> List[str]:
        return [e.target for e in self.edges if e.source == node_id]

    def get_upstream(self, node_id: str) -> List[str]:
        return [e.source for e in self.edges if e.target == node_id]


def build_default_ontology() -> ProcessOntology:
    """Build the default Petro-C → SiC process ontology."""
    onto = ProcessOntology()

    # Nodes
    onto.add_node(ProcessNode("petcoke", "Petroleum Coke", NodeType.FEEDSTOCK))
    onto.add_node(ProcessNode("silica", "SiO₂ (Quartz Sand)", NodeType.FEEDSTOCK))
    onto.add_node(ProcessNode("acid_leach", "Acid Leaching", NodeType.PROCESS,
                              properties={"T_range_C": (60, 90), "stages": "1-3"}))
    onto.add_node(ProcessNode("halogen_purify", "Halogen Purification", NodeType.PROCESS,
                              properties={"T_range_C": (1500, 2000)}))
    onto.add_node(ProcessNode("thermal", "Thermal Treatment", NodeType.PROCESS,
                              properties={"T_max_C": 1400}))
    onto.add_node(ProcessNode("purified_carbon", "Purified Carbon", NodeType.INTERMEDIATE))
    onto.add_node(ProcessNode("acheson", "Acheson Furnace", NodeType.PROCESS,
                              properties={"T_core_C": 2700, "cycle_h": 36}))
    onto.add_node(ProcessNode("sic_product", "SiC Product", NodeType.PRODUCT))
    onto.add_node(ProcessNode("electricity", "Electricity", NodeType.UTILITY))
    onto.add_node(ProcessNode("co_gas", "CO Gas (off-gas)", NodeType.WASTE))
    onto.add_node(ProcessNode("acid_waste", "Spent Acid", NodeType.WASTE))

    # Material flow edges
    for src, tgt in [
        ("petcoke", "acid_leach"),
        ("acid_leach", "halogen_purify"),
        ("halogen_purify", "thermal"),
        ("thermal", "purified_carbon"),
        ("purified_carbon", "acheson"),
        ("silica", "acheson"),
        ("acheson", "sic_product"),
        ("acheson", "co_gas"),
        ("acid_leach", "acid_waste"),
    ]:
        onto.add_edge(ProcessEdge(src, tgt, EdgeType.MATERIAL_FLOW))

    # Energy flow edges
    for tgt in ["acid_leach", "halogen_purify", "thermal", "acheson"]:
        onto.add_edge(ProcessEdge("electricity", tgt, EdgeType.ENERGY_FLOW))

    return onto
