from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

from .models import Ontology


class OntologyBackendPort(ABC):

    @abstractmethod
    def load_from_file(self, path_file: Union[str, Path]) -> Ontology:
        """Load an ontology from a local file path."""
        pass

    @abstractmethod
    def load_from_registry(self, name_id: str, format: str = "obo") -> Ontology:
        """Load an ontology from a registry/cache system, possibly downloading it."""
        pass
