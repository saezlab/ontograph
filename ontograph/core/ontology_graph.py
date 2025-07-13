from typing import Any, Dict, List, Optional

from ontograph.config.container import OntographContainer
from ontograph.core.query_engine import QueryEngine
from ontograph.ports.graph_backend import GraphBackend


class OntologyGraph:
    """Core domain entity representing an ontology as a graph structure."""

    def __init__(self, ontology: Any):
        """Initialize the ontology graph with an ontology object."""
        self.ontology = ontology
        self.graph: GraphBackend = OntographContainer.get_graph_backend(ontology)
        self.query_engine = QueryEngine(self.graph)

    def metadata(self) -> Dict[str, Any]:
        """Get basic ontology metadata."""
        meta = {
            "name": self.ontology.metadata.ontology,
            "version": self.ontology.metadata.data_version,
            "format": self.ontology.metadata.format_version,
        }
        return meta

    def get_roots(self) -> List[str]:
        """Get ontology root terms."""
        return [term.id for term in self.ontology.roots]

    def get_term(self, term_id: str) -> Optional[Any]:
        """Get details for a specific term."""
        return self.graph.get_term(term_id)

    def get_parents(self, term_id: str) -> List[str]:
        """Get immediate parent terms."""
        return self.graph.get_parents(term_id)

    def get_children(self, term_id: str) -> List[str]:
        """Get immediate child terms."""
        return self.graph.get_children(term_id)

    def get_ancestors(self, term_id: str) -> List[str]:
        """Get all ancestor terms."""
        return self.graph.get_ancestors(term_id)

    def get_descendants(self, term_id: str) -> List[str]:
        """Get all descendant terms."""
        return self.graph.get_descendants(term_id)

    def query(self, expression: str) -> List[str]:
        """Execute a query against the ontology."""
        return self.query_engine.execute(expression)
