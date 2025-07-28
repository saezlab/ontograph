import pprint
from pathlib import Path
from typing import Any, Optional

import yaml
from pooch import retrieve

from ontograph._config import (
    DEFAULT_CACHE_DIR,
    NAME_OBO_FOUNDRY_CATALOG,
    OBO_FOUNDRY_REGISTRY_URL,
)

__all__ = [
    "CatalogOntologies",
    "Ontology",
]


# -------------------------------------------------------
# ----             Catalog Ontologies Model          ----
# -------------------------------------------------------
class CatalogOntologies:

    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR) -> None:
        """Initialize the catalog manager.

        Args:
            cache_dir: Directory for caching registry files
        """
        self.cache_dir = cache_dir
        self._catalog: dict | None = None

        # Create cache directory if this one doesn't exist.
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _download_registry(self) -> Path:
        """Download the latest catalog file."""
        catalog_path = self.cache_dir / NAME_OBO_FOUNDRY_CATALOG
        retrieve(
            url=OBO_FOUNDRY_REGISTRY_URL,
            known_hash=None,
            fname=NAME_OBO_FOUNDRY_CATALOG,
            path=self.cache_dir,
        )
        return catalog_path

    def load_catalog(self, force_download: bool = False) -> str:
        catalog_path = self.cache_dir / NAME_OBO_FOUNDRY_CATALOG

        if force_download or not catalog_path.exists():
            catalog_path = self._download_registry()

        with open(catalog_path) as f:
            self._catalog = yaml.safe_load(f)

        return "Ontology successfully loaded in memory"

    @property
    def catalog(self) -> dict:
        if self._catalog is None:
            self.load_catalog()
        return self._catalog

    def list_available_ontologies(self) -> None:
        # Extract id and title of each ontology
        list_ontologies = [
            {
                "id": ont.get("id"),
                "title": ont.get("title"),
            }
            for ont in self.catalog.get("ontologies", [])
            if ont.get("id")  # Only include if it has an ID
        ]

        # Define a format to print the message
        print("{:<20} {:<40}".format("name ID", "Description"))
        print("-" * 60)

        # Print rows
        for ontology in list_ontologies:
            print(
                "{:<20} {:<40}".format(ontology.get("id", ""), ontology.get("title", ""))
            )

        return None

    def print_catalog_schema_tree(self) -> None:
        def _print_tree(
            data: list | dict, prefix: str = "", is_last: bool = True
        ) -> None:
            branch = "└── " if is_last else "├── "
            child_prefix = prefix + ("    " if is_last else "│   ")

            if isinstance(data, dict):
                # keys = list(data.keys())
                # unused variable for idx, key in enumerate(keys):
                for key in data.keys():
                    value = data[key]
                    # unused variable is_child_last = idx == len(keys) - 1
                    print(f"{prefix}{branch}{key}")
                    if isinstance(value, dict):
                        _print_tree(value, child_prefix, True)
                    elif isinstance(value, list):
                        print(f"{child_prefix}└── [list]")
                        if value:
                            _print_tree(value[0], child_prefix + "    ", True)
            elif isinstance(data, list) and data:
                _print_tree(data[0], prefix, True)

        print("\nOBO Foundry Registry Schema Structure:\n")
        _print_tree(self.catalog)

        return None

    def get_ontology_metadata(
        self,
        ontology_id: str,
        show_metadata: bool = False,
    ) -> dict | None:

        for ontology in self.catalog.get("ontologies", []):
            if ontology.get("id") == ontology_id:
                if show_metadata:
                    pprint.pprint(ontology)
                return ontology
        return None

    def get_download_url(
        self,
        ontology_id: str,
        format: str = "obo",
    ) -> str | None:
        # Get metadata from a specific ontology
        metadata = self.get_ontology_metadata(ontology_id, show_metadata=False)

        if not metadata:
            print(f"The metadata associated to {ontology_id} does not exist!")
            return None

        # Check products section
        products = metadata.get("products", [])
        for product in products:
            if product.get("id", "").lower() == f"{ontology_id.lower()}.{format.lower()}":
                return product.get("ontology_purl")

        print(
            f"Ontology '{ontology_id}' with format '.{format}' doesn't exist in the catalog!"
        )
        return None

    def get_available_formats(self, ontology_id: str) -> list[str]:

        metadata = self.get_ontology_metadata(ontology_id)
        if not metadata:
            print(f"The metadata associated to {ontology_id} does not exist!")
            return []

        formats = set()

        # Check products section
        for product in metadata.get("products", []):
            if product.get("id"):
                formats.add(product["id"].lower())

        for format in formats:
            print(format)

        return None


# ---------------------------------------------
# ----             Ontology Model          ----
# ---------------------------------------------
class Ontology:
    def __init__(
        self,
        ontology_source: Any,
        *,
        ontology_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ):
        self._ontology = ontology_source
        self._ontology_id = ontology_id
        self._metadata = metadata

    def find_path(self, source_id, target_id):
        pass

    def get_children(self, term_id: str, depth: int = -1, include_self: bool = False):
        pass

    def get_common_ancestors(self, term_ids):
        pass

    def get_depth(self, term_id):
        pass

    def get_leaves(self):
        pass

    def get_parents(self, term_id: str, depth: int = -1, include_self: bool = False):
        pass

    def get_relationships(self, term_id):
        pass

    def get_roots(self):
        pass

    def get_siblings(self, term_id):
        pass

    def get_term_info(self, term_id):
        pass

    def get_terms_by_relation(self, terms="part_of"):
        pass

    def is_descendant(self, child_id, parent_id):
        pass

    def list_terms(self, prefix="GO:", include_obsolete=False):
        pass

    def search_terms(self, query="metabolic process", exact=False):
        pass

    def term_exists(self, term_id):
        pass


# Usage example (add at the end of the file or in your script):
if __name__ == "__main__":
    # Define the path to store the registry
    path = Path("./data/out")

    # Create registry adapter object
    obo_reg = CatalogOntologies(cache_dir=path)

    # Load the registry (in case of not having the registry it will be downloaded automatically)
    obo_reg.load_catalog()

    # Print registry' schema
    obo_reg.print_catalog_schema_tree()

    # List of available ontologies
    print("Number of ontologies: {len(obo_reg.list_available_ontologies()}")

    # Print the link associated to a valid ontology (e.g., 'chebi')
    print(obo_reg.get_download_url("chebi", "obo"))

    # Print available formats for a valid ontology
    print(obo_reg.get_available_formats(ontology_id="chebi"))

    # Tip: Use obo_reg.list_available_ontologies() to find valid ontology IDs.
    print(obo_reg.list_available_ontologies())
