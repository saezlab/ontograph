from typing import Any, List, Optional

from ontograph.ports.graph_backend_port import GraphBackendPort


class ProntoGraphAdapter(GraphBackendPort):
    """Adapter implementing graph operations using Pronto."""

    def __init__(self, ontology):
        """Initialize with a Pronto ontology object."""
        self.ontology = ontology

    def get_parents(self, term_id: str) -> List[str]:
        """Get immediate parent terms."""
        term = self.ontology[term_id]
        return [parent.id for parent in term.relationships.get("is_a", [])]

    def get_children(self, term_id: str) -> List[str]:
        """Get immediate child terms."""
        term = self.ontology[term_id]
        return [child.id for child in term.subclasses()]

    def get_ancestors(self, term_id: str) -> List[str]:
        """Get all ancestor terms."""
        term = self.ontology[term_id]
        return [ancestor.id for ancestor in term.superclasses()]

    def get_descendants(self, term_id: str) -> List[str]:
        """Get all descendant terms."""
        term = self.ontology[term_id]
        return [
            descendant.id
            for descendant in term.subclasses(with_self=False, distance=None)
        ]

    def get_term(self, term_id: str) -> Optional[Any]:
        """Get term details."""
        try:
            return self.ontology[term_id]
        except KeyError:
            return None

    def get_subgraph(self, terms: List[str]) -> Any:
        """Get subgraph containing given terms and their relationships."""
        # Create a subset of the ontology with selected terms
        terms_set = set()
        for term_id in terms:
            term = self.ontology[term_id]
            terms_set.update(term.superclasses())
            terms_set.update(term.subclasses())
        return {term.id: term for term in terms_set}
