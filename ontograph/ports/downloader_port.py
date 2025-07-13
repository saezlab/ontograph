from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Union


class DownloaderPort(ABC):
    """
    Abstract interface for downloading and caching ontology files.
    """

    @abstractmethod
    def fetch(self, url: str, filename: str) -> Path:
        """
        Download a single file and return the local cached path.

        Args:
            url (str): The URL to download from
            filename (str): The name to save the file as

        Returns:
            Path: Local path to the cached file
        """
        pass

    @abstractmethod
    def fetch_batch(self, resources: List[Dict[str, str]]) -> Dict[str, Path]:
        """
        Download multiple files and return their local cached paths.

        Args:
            resources (List[Dict[str, str]]): List of dictionaries containing:
                - name_id: The ontology identifier
                - format: The file format (e.g., 'obo', 'owl')

        Returns:
            Dict[str, Path]: Dictionary mapping ontology IDs to their cached paths
        """
        pass
