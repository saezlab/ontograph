"""Provides functionality to download ontology files from URLs and catalogs.

This module defines abstract interfaces and concrete implementations for
downloading ontology resources from both direct URLs and ontology catalogs.
"""

from abc import ABC, abstractmethod
import logging
from pathlib import Path

from pooch import retrieve
import requests

from ontograph.models import CatalogOntologies
from ontograph.config.settings import DEFAULT_FORMAT_ONTOLOGY

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


__all__ = [
    'DownloadManagerAdapter',
    'DownloaderPort',
    'PoochDownloaderAdapter',
]


# -------------------------------------------------
# ----     Downloader Port (abstract class)    ----
# -------------------------------------------------
class DownloaderPort(ABC):
    """Abstract interface for ontology downloaders.

    Defines the contract for classes that can download ontologies from URLs
    or catalogs.
    """

    @abstractmethod
    def fetch_from_url(self, url_ontology: str, filename: str | None) -> Path:
        """Download an ontology file from a specified URL.

        Args:
            url_ontology: URL pointing to the ontology file
            filename: Name to save the file as

        Returns:
            Path: Path to the downloaded file

        Raises:
            ValueError: If the URL or filename is empty
            RequestException: If the download fails
            IOError: If saving the file fails
        """
        pass

    @abstractmethod
    def fetch_from_catalog(
        self, resources: list[dict[str, str]], catalog: CatalogOntologies
    ) -> dict[str, Path]:
        """Download multiple ontology files defined in a catalog.

        Args:
            resources: list of dictionaries with resource information
            catalog: Catalog object containing download URLs

        Returns:
            dict[str, Path]: dictionary mapping resource IDs to file paths

        Raises:
            ValueError: If the resources list is empty
            KeyError: If a resource is missing required fields
        """
        pass


# ----------------------------------------------------------------------
# ----       Pooch Downloader Adapter (concrete implementation)     ----
# ----------------------------------------------------------------------
class PoochDownloaderAdapter(DownloaderPort):
    """Downloader implementation using Pooch library.

    Downloads and caches ontology files using the Pooch library.
    """

    def __init__(self, cache_dir: Path) -> None:
        """Initialize the Pooch downloader.

        Args:
            cache_dir: Directory to store downloaded files
        """
        self._cache_dir = cache_dir
        self._resources_paths: dict[str, Path] = {}
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def get_paths(self) -> dict[str, Path]:
        """Get paths of all downloaded resources.

        Returns:
            dict[str, Path]: dictionary mapping resource IDs to file paths
        """
        return self._resources_paths

    def fetch_from_url(self, url_ontology: str, filename: str | None) -> Path:
        """Download an ontology file from a specified URL.

        Args:
            url_ontology: URL pointing to the ontology file
            filename: Name to save the file as

        Returns:
            Path: Path to the downloaded file

        Raises:
            ValueError: If the URL or filename is empty
            RequestException: If the download fails
            IOError: If saving the file fails
        """
        self._validate_download_parameters(url_ontology, filename)

        logging.info(f'Downloading ontology from {url_ontology} as {filename}')
        try:
            result_path = self._perform_download(url_ontology, filename)
            self._resources_paths[filename.split('.')[0]] = result_path
            return result_path
        except requests.RequestException as e:
            logging.error(f'Failed to download ontology: {e}')
            raise
        except OSError as e:
            logging.error(f'Failed to save downloaded ontology: {e}')
            raise

    def _validate_download_parameters(
        self, url_ontology: str, filename: str | None
    ) -> None:
        if not url_ontology or not url_ontology.strip():
            raise ValueError('URL cannot be empty')

        if not filename or not filename.strip():
            raise ValueError('Filename cannot be empty')

    def _perform_download(self, url_ontology: str, filename: str) -> Path:
        resource_path = retrieve(
            url=url_ontology,
            known_hash=None,  # TODO: Could later integrate SHA256 checksums
            fname=filename,
            path=self._cache_dir,
            progressbar=True,
        )
        result_path = Path(resource_path)
        logging.info(f'Successfully downloaded ontology to {result_path}')
        return result_path

    def fetch_from_catalog(
        self, resources: list[dict[str, str]], catalog: CatalogOntologies
    ) -> dict[str, Path]:
        """Download multiple ontology files defined in a catalog.

        Args:
            resources: list of dictionaries with resource information
            catalog: Catalog object containing download URLs

        Returns:
            dict[str, Path]: dictionary mapping resource IDs to file paths

        Raises:
            ValueError: If the resources list is empty or URL not found
            KeyError: If a resource is missing required fields
        """
        if not resources:
            raise ValueError('Resources list for batch download is empty.')

        results = {}
        for resource in resources:
            name_id, format_type = self._extract_resource_info(resource)
            url = self._get_resource_url(name_id, format_type, catalog)

            filename = f'{name_id}.{format_type}'
            local_path = self.fetch_from_url(
                url_ontology=url, filename=filename
            )
            results[name_id] = local_path

        self._resources_paths.update(results)
        return results

    def _extract_resource_info(
        self, resource: dict[str, str]
    ) -> tuple[str, str]:
        name_id = resource.get('name_id')
        if not name_id:
            raise KeyError("Resource dictionary must contain 'name_id' key")

        format_type = resource.get(
            'format', DEFAULT_FORMAT_ONTOLOGY
        )  # Default to OBO format
        return name_id, format_type

    def _get_resource_url(
        self, name_id: str, format_type: str, catalog: CatalogOntologies
    ) -> str:
        url = catalog.get_download_url(name_id, format_type)
        if not url:
            raise ValueError(
                f'Cannot find download URL for ontology {name_id} '
                f'in format {format_type}'
            )
        return url


# --------------------------------------------------------------------------
# ----       Downloader Manager Adapter (concrete implementation)       ----
# --------------------------------------------------------------------------
class DownloadManagerAdapter(DownloaderPort):
    """Alternative downloader implementation.

    Placeholder class for a implement the adapter using the
    `downloader-manager` by Saezlab.
    """

    pass


# -------------------------------------------------------------------------
# ----        MAIN FUNTION  (mini-sandbox to try functionalities)      ----
# -------------------------------------------------------------------------
if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)

    # Define a directory to store all the downloads
    cache = Path('./data/in')

    # Initialize a downloader object
    downloader = PoochDownloaderAdapter(cache_dir=cache)

    # Functionality 1. Download from a URL
    path_single_download = downloader.fetch_from_url(
        url_ontology='https://purl.obolibrary.org/obo/ado.owl',
        filename='adosdsdsds.owl',
    )
    print(f'Path single download: {path_single_download}')

    # Functionality 2. Download several resources from a catalog.
    from ontograph.models import CatalogOntologies

    # Download automatically the catalog
    catalog = CatalogOntologies(cache_dir=cache)
    resources = [
        {'name_id': 'go', 'format': 'obo'},
        {'name_id': 'ado', 'format': 'owl'},
    ]

    catalog = CatalogOntologies(cache_dir=cache)
    paths_resources = downloader.fetch_from_catalog(
        resources=resources, catalog=catalog
    )
    print(f'\nPaths multiple resources: {paths_resources}')

    print('\nPrint all the resources downloaded by the downloader')
    for name_id, path_resource in downloader.get_paths().items():
        print(f'\t{name_id}: {path_resource}')
