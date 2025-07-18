import pprint
from pathlib import Path

import yaml
from pooch import retrieve

from ontograph.config.settings import (
    DEFAULT_CACHE_DIR,
    OBO_FOUNDRY_REGISTRY_URL,
)

__all__ = [
    'OBORegistryAdapter',
]


class OBORegistryAdapter:
    """Manages access to the OBO Foundry ontology registry."""

    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR) -> None:
        """Initialize the registry manager.

        Args:
            cache_dir: Directory for caching registry files
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._registry: dict | None = None

    def _download_registry(self) -> Path:
        """Download the latest registry file."""
        registry_path = self.cache_dir / 'obofoundry_registry.yml'
        retrieve(
            url=OBO_FOUNDRY_REGISTRY_URL,
            known_hash=None,
            fname='obofoundry_registry.yml',
            path=self.cache_dir,
        )
        return registry_path

    def load_registry(self, force_download: bool = False) -> dict:
        """Load the OBO Foundry registry.

        Args:
            force_download: If True, download fresh copy even if cached version exists

        Returns:
            Dict: The parsed registry data
        """
        registry_path = self.cache_dir / 'obofoundry_registry.yml'

        if force_download or not registry_path.exists():
            registry_path = self._download_registry()

        with open(registry_path) as f:
            self._registry = yaml.safe_load(f)

        return 'Ontology successfully loaded in memory'

    @property
    def registry(self) -> dict:
        """Get the registry data, downloading if necessary."""
        if self._registry is None:
            self.load_registry()
        return self._registry

    def list_available_ontologies(self) -> list[dict[str, str]]:
        """Get a list of all available ontologies and their basic information.

        Returns:
            List[Dict[str, str]]: List of dictionaries containing:
                - id: The ontology ID
                - title: The ontology title
                - description: A brief description
                - homepage: URL to the ontology's homepage
                - license: License information if available
        TODO: Reviewed. Ready for improvements.
        """

        list_ontologies = [
            {
                'id': ont.get('id'),
                'title': ont.get('title'),
            }
            for ont in self.registry.get('ontologies', [])
            if ont.get('id')  # Only include if it has an ID
        ]

        print('{:<20} {:<40}'.format('name ID', 'Description'))
        print('-' * 60)

        # Print rows
        for ontology in list_ontologies:
            print(
                '{:<20} {:<40}'.format(
                    ontology.get('id', ''), ontology.get('title', '')
                )
            )

        return None

    def print_registry_schema_tree(self) -> None:
        """Print the schema of the loaded OBO Foundry registry as a tree.

        Only prints keys and [list] markers, not values or types.
        TODO: Reviewed. Ready for improvements.
        """

        def _print_tree(
            data: list | dict, prefix: str = '', is_last: bool = True
        ) -> None:
            branch = '└── ' if is_last else '├── '
            child_prefix = prefix + ('    ' if is_last else '│   ')

            if isinstance(data, dict):
                # keys = list(data.keys())
                # unused variable for idx, key in enumerate(keys):
                for key in data.keys():
                    value = data[key]
                    # unused variable is_child_last = idx == len(keys) - 1
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
        _print_tree(self.registry)

    def get_ontology_metadata(
        self, ontology_id: str, show_metadata: bool = False
    ) -> dict | None:
        """Get metadata for a specific ontology.

        Args:
            ontology_id: The ontology ID (e.g., 'go' for Gene Ontology)
            show_metadata: If True, print the metadata to the console.

        Returns:
            Optional[Dict]: The ontology metadata or None if not found.
        """
        for ontology in self.registry.get('ontologies', []):
            if ontology.get('id') == ontology_id:
                if show_metadata:
                    pprint.pprint(ontology)
                return ontology
        return None

    def get_download_url(
        self, ontology_id: str, format: str = 'obo'
    ) -> str | None:
        """Get the download URL for an ontology in a specific format.

        Args:
            ontology_id: The ontology ID
            format: The desired format ('obo' or 'owl')

        Returns:
            Optional[str]: The download URL or None if not available

        TODO: Reviewed. Ready for improvements.
        """
        metadata = self.get_ontology_metadata(ontology_id, show_metadata=False)

        if not metadata:
            print(f'The metadata associated to {ontology_id} does not exist!')
            return None

        # Check products section first (newer format)
        products = metadata.get('products', [])
        for product in products:
            if (
                product.get('id', '').lower()
                == f'{ontology_id.lower()}.{format.lower()}'
            ):
                return product.get('ontology_purl')

        print(
            f"Ontology '{ontology_id}' with format '.{format}' doesn't exist in the catalog!"
        )
        return None

    def get_available_formats(self, ontology_id: str) -> list[str]:
        """Get available formats for an ontology.

        Args:
            ontology_id: The ontology ID

        Returns:
            List[str]: List of available formats
        """
        metadata = self.get_ontology_metadata(ontology_id)
        if not metadata:
            print(f'The metadata associated to {ontology_id} does not exist!')
            return []

        formats = set()

        # Check products section
        for product in metadata.get('products', []):
            if product.get('id'):
                formats.add(product['id'].lower())

        for format in formats:
            print(format)

        return None


# Usage example (add at the end of the file or in your script):
if __name__ == '__main__':
    # Define the path to store the registry
    path = Path('./data/out')

    # Create registry adapter object
    obo_reg = OBORegistryAdapter(cache_dir=path)

    # Load the registry (in case of not having the registry it will be downloaded automatically)
    obo_reg.load_registry()

    # Print registry' schema
    obo_reg.print_registry_schema_tree()

    # List of available ontologies
    print('Number of ontologies: {len(obo_reg.list_available_ontologies()}')

    # Print the link associated to a valid ontology (e.g., 'chebi')
    print(obo_reg.get_download_url('chebi', 'obo'))

    # Print available formats for a valid ontology
    print(obo_reg.get_available_formats(ontology_id='chebi'))

    # Tip: Use obo_reg.list_available_ontologies() to find valid ontology IDs.
    print(obo_reg.list_available_ontologies())
