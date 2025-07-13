import os
from pathlib import Path
from typing import Union

import pronto
from ontograph.ports.ontology_loader import OntologyLoaderPort


class ProntoOntologyLoader(OntologyLoaderPort):
    """Adapter that loads ontologies using pronto."""

    def __init__(self, cache_dir: Union[str, Path] = None):
        """Initialize the loader with an optional cache directory."""
        self.cache_dir = Path(cache_dir) if cache_dir else Path("notebooks/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load(self, name_id: str, format: str = "obo"):
        """
        Load an ontology from a cached file.

        Args:
            name_id (str): The name/ID of the ontology file
            format (str): The format of the ontology file (obo or owl)

        Returns:
            pronto.Ontology: The loaded ontology object

        Raises:
            FileNotFoundError: If the ontology file is not found in cache
            ValueError: If the format is not supported
        """
        if format not in ["obo", "owl"]:
            raise ValueError(f"Unsupported format: {format}")

        file_path = self.cache_dir / f"{name_id}.{format}"

        if not file_path.exists():
            raise FileNotFoundError(
                f"Ontology file not found: {file_path}. "
                "Please ensure it is downloaded first."
            )

        return pronto.Ontology(str(file_path))
