"""Module for loading and parsing ontology files using the Pronto library.

This module provides functionality to load ontology files in various formats (OBO, OWL)
from a local cache directory. It implements an adapter pattern to abstract the details
of the Pronto library, providing a simpler interface for loading ontologies.

Typical usage example:
    >>> from ontograph.ontology_loader import ProntoLoaderAdapter
    >>> loader = ProntoLoaderAdapter("./cache")
    >>> go_ontology = loader.load("go", format="obo")
"""

from pathlib import Path

from pronto.ontology import Ontology

from ontograph.downloader import PoochDownloaderAdapter
from ontograph.config.settings import DEFAULT_CACHE_DIR
from ontograph.ontology_registry import OBORegistryAdapter

__all__ = [
    'ProntoLoaderAdapter',
]


class ProntoLoaderAdapter:
    """Adapter that loads ontologies using Pronto library.

    This class provides an adapter interface for loading ontology files using the Pronto
    library. It supports loading both OBO and OWL format files from a local cache
    directory.

    Attributes:
        cache_dir (Path): Directory where ontology files are cached.
    """

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        """Initialize the loader with an optional cache directory.

        Args:
            cache_dir (str | Path | None, optional): Path to the cache directory.
                If None, uses the default cache directory from settings.
                Defaults to None.

        Note:
            Creates the cache directory if it doesn't exist.
        """
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR

    def load_from_file(self, path_file: str) -> Ontology:
        """Loads an ontology from the specified file path.

        Args:
            path_file (str): The path to the ontology file.

        Returns:
            Ontology: The loaded ontology object if successful.

        Raises:
            TypeError: If the ontology cannot be loaded due to a type error.
            ValueError: If the ontology cannot be loaded due to a value error.

        Prints:
            Status messages indicating the progress and result of the loading process.
        """
        path_file = Path(path_file)
        if path_file.exists():
            print('Loading ontology...')
            try:
                ontology = Ontology(path_file)
            except TypeError:
                print('The ontology cannot be loaded')
            except ValueError:
                print('The ontology cannot be loaded')
            print('Ontology successfully loaded!!!')
            return ontology

    def load_from_registry(self, name_id: str, format: str = 'obo') -> Ontology:
        """Load an ontology from a cached file.

        This method loads an ontology file from the cache directory and parses it
        using the Pronto library. The file must exist in the cache directory before
        calling this method.

        Args:
            name_id (str): The name/ID of the ontology file to load (e.g., 'go' for
                Gene Ontology, 'chebi' for Chemical Entities of Biological Interest).
            format (str, optional): The format of the ontology file.
                Must be either 'obo' or 'owl'. Defaults to 'obo'.

        Returns:
            Ontology: A Pronto Ontology object containing the full ontology structure,
                including terms, relationships, and metadata.

        Raises:
            FileNotFoundError: If the ontology file '{name_id}.{format}' is not found
                in the cache directory. Ensure the file is downloaded first.
            ValueError: If the format is not one of the supported formats ('obo', 'owl').

        Example:
            Load the Gene Ontology in OBO format:

            >>> loader = ProntoLoaderAdapter("./cache")
            >>> go_ontology = loader.load("go", format="obo")
            >>> print(f"Loaded {len(go_ontology.terms())} terms")
            Loaded 50000 terms
        """
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if format not in ['obo', 'owl']:
            raise ValueError(f'Unsupported format: {format}')

        file_path = self.cache_dir / f'{name_id}.{format}'

        if not file_path.exists():
            print(
                f'Ontology file not found: {file_path}. '
                'Please ensure it is downloaded first.'
            )
            print('Downloading ontology...')
            # Load registry
            onto_registry = OBORegistryAdapter(cache_dir=self.cache_dir)

            # Instantiate downloader
            ontology_downloader = PoochDownloaderAdapter(
                cache_dir=self.cache_dir, registry=onto_registry
            )

            # Download resources
            resources = [
                {
                    'name_id': name_id,
                    'format': format,
                },
            ]
            file_path = ontology_downloader.fetch_batch(resources=resources)
            file_path = file_path.get(name_id)

            print(f'My ontology path: {file_path}')

            print(f'Ontology downloaded? {file_path.exists()}')
            print('Ontology successfully downloaded!')

        try:
            print('Loading ontology...`')
            ontology = Ontology(file_path)
        except TypeError:
            print('The ontology cannot be loaded')
        except ValueError:
            print('The ontology is in an unsupported format')
        print('Ontology successfully loaded!!!')

        return ontology


if __name__ == '__main__':
    # Example usage of ProntoLoaderAdapter
    cache_dir = 'data/out'  # or any directory where ontology files are cached
    loader = ProntoLoaderAdapter(cache_dir=cache_dir)

    # Example: Load a cached ontology file (must exist in cache_dir)
    ontology_id = 'go'  # Use a valid ontology ID
    format = 'obo'
    try:
        ontology = loader.load_from_registry(ontology_id, format)
        print(f'Loaded ontology: {ontology_id}.{format}')
        print(f'Number of terms: {len(ontology.terms())}')
    except FileNotFoundError as e:
        print(e)
    except ValueError as e:
        print(e)
