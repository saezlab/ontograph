from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class OntologyRegistryPort(ABC):
    """
    Port interface for accessing ontology registry metadata and download information.
    Defines the contract for registry adapters, supporting Hexagonal Architecture.
    """

    @abstractmethod
    def list_available_ontologies(self) -> List[Dict[str, str]]:
        """
        Retrieve a list of available ontologies from the registry.
        Returns:
            List[Dict[str, str]]: Each dict contains ontology metadata (id, name, etc.).
        """
        pass

    @abstractmethod
    def get_ontology_metadata(self, ontology_id: str) -> Optional[Dict]:
        """
        Retrieve metadata for a specific ontology by its ID.
        Args:
            ontology_id (str): The unique identifier for the ontology.
        Returns:
            Optional[Dict]: Metadata dictionary if found, else None.
        """
        pass

    @abstractmethod
    def get_download_url(self, ontology_id: str, format: str = "obo") -> Optional[str]:
        """
        Get the download URL for an ontology in a specific format.
        Args:
            ontology_id (str): The unique identifier for the ontology.
            format (str): Desired file format (e.g., 'obo', 'owl'). Defaults to 'obo'.
        Returns:
            Optional[str]: Download URL if available, else None.
        """
        pass

    @abstractmethod
    def get_available_formats(self, ontology_id: str) -> List[str]:
        """
        List all available formats for a given ontology.
        Args:
            ontology_id (str): The unique identifier for the ontology.
        Returns:
            List[str]: Supported formats (e.g., ['obo', 'owl', 'json']).
        """
        pass
