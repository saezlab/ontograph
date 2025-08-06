import pprint
import logging
from pathlib import Path

import yaml
from pooch import retrieve

from ontograph.config.settings import (
    DEFAULT_CACHE_DIR,
    NAME_OBO_FOUNDRY_CATALOG,
    OBO_FOUNDRY_REGISTRY_URL,
)

__all__ = ['CatalogOntologies', 'Ontology']

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class CatalogOntologies:
    """Manages the OBO Foundry catalog of ontologies.

    Provides methods to download, load, and query the ontology registry.
    """

    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR) -> None:
        """Initialize the catalog manager.

        Args:
            cache_dir (Path): Directory for caching registry files.
        """
        self.cache_dir = cache_dir
        self._catalog: dict | None = None

        # Create cache directory if this one doesn't exist.
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _download_registry(self) -> Path:
        """Download the latest catalog file.

        Returns:
            Path: Path to the downloaded catalog file.
        """
        catalog_path = self.cache_dir / NAME_OBO_FOUNDRY_CATALOG
        retrieve(
            url=OBO_FOUNDRY_REGISTRY_URL,
            known_hash=None,
            fname=NAME_OBO_FOUNDRY_CATALOG,
            path=self.cache_dir,
        )
        return catalog_path

    def load_catalog(self, force_download: bool = False) -> None:
        """Load the ontology catalog from disk or download if needed.

        Args:
            force_download (bool): If True, force download the catalog file.
        """
        catalog_path = self.cache_dir / NAME_OBO_FOUNDRY_CATALOG

        if force_download or not catalog_path.exists():
            catalog_path = self._download_registry()

        with open(catalog_path) as f:
            self._catalog = yaml.safe_load(f)

        return None

    @property
    def catalog(self) -> dict:
        """Return the loaded catalog as a dictionary.

        Returns:
            dict: The loaded catalog.
        """
        if self._catalog is None:
            self.load_catalog()
        return self._catalog

    def list_available_ontologies(self) -> list[dict]:
        """List available ontologies with their IDs and titles.

        Returns:
            list[dict]: List of ontologies with 'id' and 'title'.
        """
        list_ontologies = [
            {
                'id': ont.get('id'),
                'title': ont.get('title'),
            }
            for ont in self.catalog.get('ontologies', [])
            if ont.get('id')  # Only include if it has an ID
        ]

        return list_ontologies

    def print_available_ontologies(self) -> None:
        """Print the available ontologies in a formatted table."""
        list_ontologies = self.list_available_ontologies()

        print('{:<20} {:<40}'.format('name ID', 'Description'))
        print('-' * 60)

        for ontology in list_ontologies:
            print(
                '{:<20} {:<40}'.format(
                    ontology.get('id', ''), ontology.get('title', '')
                )
            )

    def print_catalog_schema_tree(self) -> None:
        """Print the schema structure of the OBO Foundry registry."""

        def _print_tree(
            data: list | dict, prefix: str = '', is_last: bool = True
        ) -> None:
            branch = '└── ' if is_last else '├── '
            child_prefix = prefix + ('    ' if is_last else '│   ')

            if isinstance(data, dict):
                for key in data.keys():
                    value = data[key]
                    print(f'{prefix}{branch}{key}')
                    if isinstance(value, dict):
                        _print_tree(value, child_prefix, True)
                    elif isinstance(value, list):
                        print(f'{child_prefix}└── [list]')
                        if value:
                            _print_tree(value[0], child_prefix + '    ', True)
            elif isinstance(data, list) and data:
                _print_tree(data[0], prefix, True)

        print('\nOBO Foundry Registry Schema Structure:\n')
        _print_tree(self.catalog)

        return None

    def get_ontology_metadata(
        self,
        ontology_id: str,
        show_metadata: bool = False,
    ) -> dict:
        """Retrieve metadata for a specific ontology.

        Args:
            ontology_id (str): Ontology identifier.
            show_metadata (bool): If True, pretty-print the metadata.

        Returns:
            dict: Metadata dictionary for the ontology.

        Raises:
            Exception: If metadata is not found.
        """
        try:
            for ontology in self.catalog.get('ontologies', []):
                if ontology.get('id') == ontology_id:
                    if show_metadata:
                        pprint.pprint(ontology)
                    return ontology
        except Exception as e:
            logger.exception(f'Metadata not found!: {e}')
            raise

    def get_download_url(
        self,
        ontology_id: str,
        format: str = 'obo',
    ) -> str:
        """Retrieve the download URL for a specific ontology and format.

        Args:
            ontology_id (str): Identifier of the ontology.
            format (str): Desired ontology file format (default: 'obo').

        Returns:
            str: The download URL (ontology_purl).

        Raises:
            ValueError: If the ontology or the specified format is not found in the catalog.
        """
        metadata = self.get_ontology_metadata(ontology_id, show_metadata=False)
        if metadata is None:
            raise ValueError(
                f"No metadata found for ontology ID '{ontology_id}'."
            )

        expected_id = f'{ontology_id.lower()}.{format.lower()}'
        products = metadata.get('products', [])

        for product in products:
            if product.get('id', '').lower() == expected_id:
                purl = product.get('ontology_purl')
                if purl:
                    return purl
                break  # Matching ID found but no URL

        raise ValueError(
            f"Download URL not found for ontology '{ontology_id}' with format '.{format}'."
        )

    def get_available_formats(self, ontology_id: str) -> list[str]:
        """Get available formats for a given ontology.

        Args:
            ontology_id (str): Ontology identifier.

        Returns:
            list[str]: List of available formats.
        """
        metadata = self.get_ontology_metadata(ontology_id)
        if not metadata:
            print(f'The metadata associated to {ontology_id} does not exist!')
            return []

        formats = set()

        for product in metadata.get('products', []):
            if product.get('id'):
                formats.add(product['id'].lower())

        return list(formats)


class Ontology:
    """Represents an ontology loaded from a source."""

    def __init__(
        self,
        ontology_source: object,
        *,
        ontology_id: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Initialize the Ontology object.

        Args:
            ontology_source (Any): The loaded ontology object.
            ontology_id (str | None, optional): Ontology identifier.
            metadata (dict | None, optional): Metadata dictionary.
        """
        self._ontology = ontology_source
        self._ontology_id = ontology_id
        self._metadata = metadata

    def get_ontology(self) -> object:
        """Return the underlying ontology object.

        Returns:
            Any: The loaded ontology object.
        """
        return self._ontology

    def get_ontology_id(self) -> str | None:
        """Return the ontology identifier.

        Returns:
            str | None: The ontology ID.
        """
        return self._ontology_id

    def get_metadata(self) -> dict | None:
        """Return the ontology metadata.

        Returns:
            dict | None: The metadata dictionary.
        """
        return self._metadata
