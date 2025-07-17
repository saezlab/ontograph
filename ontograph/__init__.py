from ontograph.ontology_registry import OBORegistryAdapter
from ontograph.ontology_loader import ProntoLoaderAdapter

from ontograph.config.settings import DEFAULT_CACHE_DIR
from pathlib import Path

cache_dir = DEFAULT_CACHE_DIR


# Public API
def registry(cache_dir: str | None) -> OBORegistryAdapter:
    """
    Entry point for accessing ontology registry.
    """
    registry = OBORegistryAdapter(cache_dir=Path(cache_dir))
    return registry
