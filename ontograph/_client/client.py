from pathlib import Path
from typing import Optional


from ontograph._config import DEFAULT_CACHE_DIR

# from ontograph.ontology_loader import ProntoLoaderAdapter
# from ontograph.ontology_registry import OBORegistryAdapter


from ontograph._utils.registry import get_adapter
from ontograph._utils.registry import AdapterRegistry
from ontograph._core.models import CatalogOntologies
from ontograph._core.models import Ontology


# ------------------------------------------------------
# ----      Orchestration between components        ----
# ------------------------------------------------------
class CatalogClient:
    def __init__(self, cache_dir: Path = Path(DEFAULT_CACHE_DIR)) -> None:
        self.__catalog_adapter = CatalogOntologies(cache_dir=cache_dir)

    def load_catalog(self, force_download: bool = False) -> None:
        return self.__catalog_adapter.load_catalog(force_download=force_download)

    def catalog(self) -> dict:
        return self.__catalog_adapter.catalog

    def list_available_ontologies(self) -> None:
        return self.__catalog_adapter.list_available_ontologies()

    def print_catalog_schema_tree(self) -> None:
        return self.__catalog_adapter.print_catalog_schema_tree()

    def get_ontology_metadata(
        self,
        ontology_id: str,
        show_metadata: bool = False,
    ) -> dict | None:
        return self.__catalog_adapter.get_ontology_metadata(
            ontology_id=ontology_id,
            show_metadata=show_metadata,
        )

    def get_download_url(
        self,
        ontology_id: str,
        format: str = "obo",
    ) -> str | None:
        return self.__catalog_adapter.get_download_url(
            ontology_id=ontology_id, format=format
        )

    def get_available_formats(self, ontology_id: str) -> list[str]:
        return self.__catalog_adapter.get_available_formats(ontology_id=ontology_id)


class OntologyClient:
    def __init__(self, backend: Optional[str] = None):
        adapter_cls = get_adapter(backend)  # Will use default if None
        self.loader = adapter_cls  # Store the class, not an instance

    def load(
        self,
        *,
        path: str = None,
        name_id: str = None,
        format: str = "obo",
        cache_dir: Path = Path(DEFAULT_CACHE_DIR),
    ) -> Ontology:
        # Create instance with cache_dir when needed
        loader = self.loader(cache_dir=cache_dir)

        if path is not None:
            path_obj = Path(path)
            if path_obj.exists():
                return loader.load_from_file(path_file=path_obj)
            else:
                raise ValueError(f"Provided path does not exist: {path}")
        elif name_id is not None:
            return loader.load_from_registry(name_id=name_id, format=format)
        else:
            raise ValueError("Either 'path' or 'name_id' must be provided.")


# ------------------------------------------------------
# ----      Final Functions for users               ----
# ------------------------------------------------------
def catalog(cache_dir: Path = Path(DEFAULT_CACHE_DIR)):
    """Create a catalog client."""
    catalog_client = CatalogClient(cache_dir=Path(cache_dir))
    catalog_client.load_catalog(force_download=False)
    return catalog_client


def load(
    path: str = None,
    name_id: str = None,
    format: str = "obo",
    cache_dir: Path = Path(DEFAULT_CACHE_DIR),
    *,
    backend: Optional[str] = None,  # Make it optional
) -> Ontology:
    ontology_client = OntologyClient(backend=backend)

    return ontology_client.load(
        path=path, name_id=name_id, format=format, cache_dir=cache_dir
    )


def get_available_backends() -> list[str]:
    """
    Get a list of available backend adapters.

    Returns:
        List of backend names
    """
    return AdapterRegistry.list_adapters()
