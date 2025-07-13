from abc import ABC, abstractmethod
from typing import Any, List, Optional, Protocol


class GraphBackendPort(ABC):
    """Port defining graph operations interface."""

    @abstractmethod
    def get_parents(self, term_id: str) -> List[str]:
        """Get parent terms."""
        pass

    @abstractmethod
    def get_children(self, term_id: str) -> List[str]:
        """Get child terms."""
        pass

    @abstractmethod
    def get_ancestors(self, term_id: str) -> List[str]:
        """Get all ancestor terms."""
        pass

    @abstractmethod
    def get_descendants(self, term_id: str) -> List[str]:
        """Get all descendant terms."""
        pass

    @abstractmethod
    def get_term(self, term_id: str) -> Optional[Any]:
        """Get term details."""
        pass

    @abstractmethod
    def get_subgraph(self, terms: List[str]) -> Any:
        """Get subgraph containing given terms."""
        pass


class OntologyProtocol(Protocol):
    """Protocol defining required Ontology interface."""

    @property
    def metadata(self) -> Any: ...
    def __getitem__(self, key: str) -> Any: ...
