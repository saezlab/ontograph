from pathlib import Path
from typing import Dict, List, Optional

from pooch import retrieve

from ontograph.adapters.obo_foundry_registry import OBOFoundryRegistry
from ontograph.ports.downloader import AbstractDownloader


class PoochDownloader(AbstractDownloader):
    """
    Concrete downloader using Pooch for caching ontology files.
    """

    def __init__(self, cache_dir: Path = Path.home() / ".ontograph_cache"):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.registry = OBOFoundryRegistry(cache_dir)

    def _get_download_url(self, name_id: str, format: str) -> Optional[str]:
        """Get download URL from registry."""
        return self.registry.get_download_url(name_id, format)

    def fetch(self, url: str, filename: str) -> Path:
        """
        Download a file from `url` and cache it locally.

        Args:
            url (str): The URL to download.
            filename (str): The name to save the file as.

        Returns:
            Path: Local path to the cached file.
        """
        local_file = retrieve(
            url=url,
            known_hash=None,  # Could later integrate SHA256 checksums
            fname=filename,
            path=self.cache_dir,
        )
        return Path(local_file)

    def fetch_batch(self, resources: List[Dict[str, str]]) -> Dict[str, Path]:
        """
        Download multiple ontology files and cache them locally.

        Args:
            resources (List[Dict[str, str]]): List of dictionaries containing:
                - name_id: The ontology identifier
                - format: The file format (e.g., 'obo', 'owl')

        Returns:
            Dict[str, Path]: Dictionary mapping ontology IDs to their cached paths

        Raises:
            ValueError: If an ontology is not found or format is not supported
            KeyError: If required keys are missing in the resource dictionary
        """
        results = {}

        for resource in resources:
            name_id = resource.get("name_id")
            format = resource.get("format", "obo")  # Default to OBO format

            if not name_id:
                raise KeyError("Resource dictionary must contain 'name_id' key")

            # Get URL from registry
            url = self._get_download_url(name_id, format)
            if not url:
                raise ValueError(
                    f"Cannot find download URL for ontology {name_id} "
                    f"in format {format}"
                )

            filename = f"{name_id}.{format}"
            local_path = self.fetch(url, filename)
            results[name_id] = local_path

        return results

    def list_available_ontologies(self) -> List[Dict[str, str]]:
        """
        Get list of available ontologies from the registry.

        Returns:
            List[Dict[str, str]]: List of available ontologies with their metadata
        """
        return self.registry.list_available_ontologies()

    def get_available_formats(self, ontology_id: str) -> List[str]:
        """
        Get available formats for an ontology.

        Args:
            ontology_id: The ontology identifier

        Returns:
            List[str]: List of available formats
        """
        return self.registry.get_available_formats(ontology_id)

    def get_ontology_metadata(self, ontology_id: str) -> Optional[Dict]:
        """
        Get detailed metadata for an ontology.

        Args:
            ontology_id: The ontology identifier

        Returns:
            Optional[Dict]: The ontology metadata or None if not found
        """
        return self.registry.get_ontology_metadata(ontology_id)
