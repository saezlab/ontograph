from pathlib import Path
from typing import Dict, List, Optional

from pooch import retrieve


from ontograph.ontology_registry import OBORegistryAdapter


class PoochDownloaderAdapter:
    """
    Concrete downloader using Pooch for caching ontology files.
    """

    def __init__(self, cache_dir: Path, registry: OBORegistryAdapter):
        """
        Initialize the downloader adapter.

        Args:
            cache_dir (Path): Directory for caching downloaded files
            registry (OBORegistryAdapter): Registry port for resolving download URLs
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.registry = registry

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
            progressbar=True,
        )
        return Path(local_file)

    def fetch_batch(self, resources: List[Dict[str, str]]) -> Dict[str, Path]:
        """
        Download multiple ontology files and cache them locally.

        Args:
            resources (List[Dict[str, str]]): List of dictionaries containing:
                - name_id: The ontology identifier
                - format: The file format (e.g., 'obo', 'owl'). Defaults to 'obo' if not specified.

        Returns:
            Dict[str, Path]: Dictionary mapping ontology IDs to their cached paths

        Raises:
            ValueError: If resources list is empty, an ontology is not found, or format is not supported
            KeyError: If required keys are missing in the resource dictionary
        """
        if not resources:
            raise ValueError("Resources list for batch download is empty.")

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


if __name__ == "__main__":
    from ontograph.ontology_registry import OBORegistryAdapter

    # Defines the cache directory
    cache_dir = Path("./data/out")

    # Creates a registry object (real implementation OBORegistryAdapter)
    registry = OBORegistryAdapter(cache_dir=cache_dir)
    registry.load_registry()

    # Creates a downloader object
    downloader = PoochDownloaderAdapter(cache_dir=cache_dir, registry=registry)

    ## Example 1. Download a single ontology file from the registry
    ontology_id = "ado"
    format = "owl"

    # Extract the url from the registry
    url = registry.get_download_url(ontology_id, format)

    if url:
        # Downloads the file
        local_path = downloader.fetch(url=url, filename=f"{ontology_id}.{format}")
        print(f"Downloaded {ontology_id}.{format} to: {local_path}")

    ## Example 2. Batch download
    resources = [
        {"name_id": "chebi", "format": "owl"},
        {"name_id": "go", "format": "obo"},
    ]
    batch_results = downloader.fetch_batch(resources)
    print("Batch download results:", batch_results)
