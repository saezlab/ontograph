from typing import List

from ontograph.ports.graph_backend_port import GraphBackendPort


class QueryEngine:
    """Core domain service for querying the ontology graph."""

    def __init__(self, graph: GraphBackendPort):
        """Initialize with a graph backend."""
        self.graph = graph

    def execute(self, expression: str) -> List[str]:
        """
        Execute a query expression against the ontology.

        Currently supports basic operations:
        - ancestors:term_id - get all ancestors of a term
        - descendants:term_id - get all descendants of a term
        - parents:term_id - get immediate parents of a term
        - children:term_id - get immediate children of a term
        """
        op, term_id = expression.split(":")

        if op == "ancestors":
            return self.graph.get_ancestors(term_id)
        elif op == "descendants":
            return self.graph.get_descendants(term_id)
        elif op == "parents":
            return self.graph.get_parents(term_id)
        elif op == "children":
            return self.graph.get_children(term_id)
        else:
            raise ValueError(f"Unsupported operation: {op}")
