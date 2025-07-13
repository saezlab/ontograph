from abc import ABC, abstractmethod


class OntologyLoaderPort(ABC):
    """Defines a contract for ontology loading."""

    @abstractmethod
    def load(self, name_id: str, format: str):
        pass
