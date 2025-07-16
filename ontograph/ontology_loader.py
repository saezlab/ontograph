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

from ontograph.config.settings import DEFAULT_CACHE_DIR

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
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load(self, name_id: str, format: str = 'obo') -> Ontology:
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
        if format not in ['obo', 'owl']:
            raise ValueError(f'Unsupported format: {format}')

        file_path = self.cache_dir / f'{name_id}.{format}'

        if not file_path.exists():
            raise FileNotFoundError(
                f'Ontology file not found: {file_path}. '
                'Please ensure it is downloaded first.'
            )

        return Ontology(str(file_path))


if __name__ == '__main__':
    # Example usage of ProntoLoaderAdapter
    cache_dir = 'data/out'  # or any directory where ontology files are cached
    loader = ProntoLoaderAdapter(cache_dir=cache_dir)

    # Example: Load a cached ontology file (must exist in cache_dir)
    ontology_id = 'go'  # Use a valid ontology ID
    format = 'obo'
    try:
        ontology = loader.load(ontology_id, format)
        print(f'Loaded ontology: {ontology_id}.{format}')
        print(f'Number of terms: {len(ontology.terms())}')
    except FileNotFoundError as e:
        print(e)
    except ValueError as e:
        print(e)
