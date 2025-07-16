from pathlib import Path

from pronto.ontology import Ontology

__all__ = [
    'ProntoLoaderAdapter',
]


class ProntoLoaderAdapter:
    """Adapter that loads ontologies using pronto."""

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        """Initialize the loader with an optional cache directory."""
        self.cache_dir = (
            Path(cache_dir) if cache_dir else Path('notebooks/cache')
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load(self, name_id: str, format: str = 'obo') -> Ontology:
        """Load an ontology from a cached file.

        Args:
            name_id (str): The name/ID of the ontology file
            format (str): The format of the ontology file (obo or owl)

        Returns:
            pronto.ontology.Ontology: The loaded ontology object

        Raises:
            FileNotFoundError: If the ontology file is not found in cache
            ValueError: If the format is not supported
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
