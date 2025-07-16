"""Module for downloading and caching ontology files.

This module provides functionality to download ontology files from various sources
and cache them locally for efficient access. It implements an adapter pattern
around the Pooch library for download and caching management.

The module supports:
    - Single file downloads with caching
    - Batch downloads of multiple ontology files
    - Multiple ontology formats (OBO, OWL)
    - URL resolution through a registry system

Typical usage example:
    >>> from ontograph.downloader import PoochDownloaderAdapter
    >>> from ontograph.ontology_registry import OBORegistryAdapter
    >>>
    >>> registry = OBORegistryAdapter(cache_dir="./cache")
    >>> downloader = PoochDownloaderAdapter(cache_dir="./cache", registry=registry)
    >>> path = downloader.fetch_batch([{"name_id": "go", "format": "obo"}])
"""

from pathlib import Path

from pooch import retrieve

from ontograph.ontology_registry import OBORegistryAdapter

__all__ = [
    'PoochDownloaderAdapter',
]


class PoochDownloaderAdapter:
    """Concrete downloader using Pooch for caching ontology files.

    This class implements a downloader adapter using the Pooch library to handle
    downloading and caching of ontology files. It provides a simplified interface
    for downloading ontology files while handling caching and file management
    automatically.

    The adapter integrates with an ontology registry to resolve download URLs
    and supports both single-file and batch download operations.

    Attributes:
        cache_dir (Path): Directory where downloaded files are cached.
        registry (OBORegistryAdapter): Registry instance used to resolve ontology URLs.
    """

    def __init__(self, cache_dir: Path, registry: OBORegistryAdapter) -> None:
        """Initialize the downloader adapter.

        Args:
            cache_dir (Path): Directory for caching downloaded files.
            registry (OBORegistryAdapter): Registry port for resolving download URLs.

        Returns:
            None
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.registry = registry

    def _get_download_url(self, name_id: str, format: str) -> str | None:
        """Get download URL for an ontology from the registry.

        Internal method that resolves the download URL for a given ontology
        identifier and format using the configured registry.

        Args:
            name_id (str): The ontology identifier (e.g., 'go', 'chebi').
            format (str): The desired file format (e.g., 'obo', 'owl').

        Returns:
            str | None: The download URL if found in the registry, None if the
                ontology or format is not available.

        Note:
            This is an internal method used by `fetch` and `fetch_batch`.
            The URL resolution depends on the registry's configuration.
        """
        return self.registry.get_download_url(name_id, format)

    def fetch(self, url: str, filename: str) -> Path:
        """Download a file from URL and cache it locally.

        Downloads an ontology file from the specified URL and saves it in the cache
        directory. If the file already exists in the cache, it will be reused
        unless it's outdated.

        Args:
            url (str): The complete URL to download the ontology file from.
            filename (str): The name to save the file as in the cache directory.
                Should include the appropriate extension (.obo or .owl).

        Returns:
            Path: Absolute path to the cached file in the local filesystem.

        Example:
            >>> downloader = PoochDownloaderAdapter("./cache", registry)
            >>> path = downloader.fetch(
            ...     "http://purl.obolibrary.org/obo/go.obo",
            ...     "go.obo"
            ... )
            >>> print(path)
            /path/to/cache/go.obo

        Note:
            This method uses Pooch's retrieve function which handles:
            - File download with progress bar
            - Caching mechanism
            - Future: File integrity verification (SHA256)
        """
        local_file = retrieve(
            url=url,
            known_hash=None,  # Could later integrate SHA256 checksums
            fname=filename,
            path=self.cache_dir,
            progressbar=True,
        )
        return Path(local_file)

    def fetch_batch(self, resources: list[dict[str, str]]) -> dict[str, Path]:
        """Download multiple ontology files and cache them locally.

        This method provides batch downloading capability for multiple ontology files.
        Each resource in the input list specifies an ontology to download. The URLs
        are resolved through the registry, and all files are cached locally.

        Args:
            resources (list[dict[str, str]]): List of dictionaries, where each
                dictionary must contain:
                - name_id (str): The ontology identifier (e.g., 'go', 'chebi')
                - format (str, optional): File format ('obo' or 'owl').
                    Defaults to 'obo'

        Returns:
            dict[str, Path]: Dictionary mapping ontology IDs to their cached paths.
                For example:
                {
                    'go': Path('/path/to/cache/go.obo'),
                    'chebi': Path('/path/to/cache/chebi.owl')
                }

        Raises:
            ValueError: In the following cases:
                - Empty resources list provided
                - Ontology not found in registry
                - Unsupported format specified
            KeyError: If 'name_id' key is missing in any resource dictionary

        Example:
            Download Gene Ontology and ChEBI in different formats:

            >>> downloader = PoochDownloaderAdapter("./cache", registry)
            >>> resources = [
            ...     {"name_id": "go", "format": "obo"},
            ...     {"name_id": "chebi", "format": "owl"}
            ... ]
            >>> paths = downloader.fetch_batch(resources)
            >>> for ontology_id, path in paths.items():
            ...     print(f"{ontology_id}: {path}")
            go: /path/to/cache/go.obo
            chebi: /path/to/cache/chebi.owl

        """
        if not resources:
            raise ValueError('Resources list for batch download is empty.')

        results = {}

        for resource in resources:
            name_id = resource.get('name_id')
            format = resource.get('format', 'obo')  # Default to OBO format

            if not name_id:
                raise KeyError("Resource dictionary must contain 'name_id' key")

            # Get URL from registry
            url = self._get_download_url(name_id, format)
            if not url:
                raise ValueError(
                    f'Cannot find download URL for ontology {name_id} '
                    f'in format {format}'
                )

            filename = f'{name_id}.{format}'
            local_path = self.fetch(url, filename)
            results[name_id] = local_path

        return results
