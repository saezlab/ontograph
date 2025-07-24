from pathlib import Path

from pronto.ontology import Ontology

from ontograph.config.settings import DEFAULT_CACHE_DIR
from ontograph.ontology_loader import ProntoLoaderAdapter
from ontograph.ontology_registry import OBORegistryAdapter

__all__ = [
    'OntoRegistryClient',
    'load',
    'registry',
]


class OntoRegistryClient:
    """Client for interacting with the ontology registry.

    This class provides methods to interact with the ontology registry,
    including loading the registry, retrieving metadata, and listing available ontologies.
    """

    def __init__(self, cache_dir: Path = Path(DEFAULT_CACHE_DIR)) -> None:
        """Initialize the OntoRegistryClient.

        Args:
            cache_dir (Path, optional): The directory to use for caching registry data. Defaults to DEFAULT_CACHE_DIR.
        """
        self.__registry_adapter = OBORegistryAdapter(cache_dir=cache_dir)

    def load_registry(self, force_download: bool = False) -> None:
        """Load the ontology registry.

        Args:
            force_download (bool, optional): Whether to force downloading the registry data. Defaults to False.
        """
        return self.__registry_adapter.load_registry(
            force_download=force_download
        )

    def registry_as_dict(self) -> dict:
        """Retrieve the ontology registry as a dictionary.

        Returns:
            dict: The ontology registry represented as a dictionary.
        """
        return self.__registry_adapter.registry

    def list_available_ontologies(self) -> list[str]:
        """List all available ontologies in the registry.

        Returns:
            list[str]: A list of ontology identifiers available in the registry.
        """
        return self.__registry_adapter.list_available_ontologies()

    def print_registry_schema_tree(self) -> None:
        """Print the schema tree of the ontology registry."""
        self.__registry_adapter.print_registry_schema_tree()

    def get_ontology_metadata(
        self, ontology_id: str, show_metadata: bool = False
    ) -> dict:
        """Retrieve metadata for a specific ontology.

        Args:
            ontology_id (str): The identifier of the ontology.
            show_metadata (bool, optional): Whether to include detailed metadata. Defaults to False.

        Returns:
            dict: A dictionary containing metadata for the specified ontology.
        """
        return self.__registry_adapter.get_ontology_metadata(
            ontology_id, show_metadata=show_metadata
        )

    def get_download_url(self, ontology_id: str, format: str = 'obo') -> str:
        """Retrieve the download URL for a specific ontology in a given format.

        Args:
            ontology_id (str): The identifier of the ontology.
            format (str, optional): The format of the ontology (e.g., 'obo', 'json'). Defaults to 'obo'.

        Returns:
            str: The download URL for the specified ontology and format.
        """
        return self.__registry_adapter.get_download_url(ontology_id, format)

    def get_available_formats(self, ontology_id: str) -> list[str]:
        """Retrieve the list of available formats for a given ontology.

        Args:
            ontology_id (str): The identifier of the ontology.

        Returns:
            list[str]: A list of strings representing the available formats for the ontology.
        """
        return self.__registry_adapter.get_available_formats(ontology_id)


# class OntologyClient:
#     """Client for interacting with a specific ontology."""

#     def __init__(self, ontology: Ontology):
#         self.queries = OntologyQueries(ontology)

#     def get_parents(self, term_id: str, depth: int = -1, include_self: bool = False):
#         return self.queries.ancestors(term_id, include_self=include_self)

#     def get_children(self, term_id: str, depth: int = -1, include_self: bool = False):
#         return self.queries.descendants(term_id, include_self=include_self)

#     def get_siblings(self, term_id: str):
#         parents = self.queries.parent(term_id)
#         siblings = set()
#         for parent in parents:
#             siblings.update(self.queries.children(parent))
#         siblings.discard(term_id)
#         return siblings

#     def get_roots(self):
#         return [term.id for term in self.queries.ont if not term.superclasses()]

#     def get_leaves(self):
#         return [term.id for term in self.queries.ont if not term.subclasses()]

#     def find_path(self, source_id: str, target_id: str):
#         # Implement pathfinding logic if needed
#         pass

#     def is_descendant(self, child_id: str, parent_id: str):
#         return child_id in self.queries.descendants(parent_id)

#     def get_depth(self, term_id: str):
#         # Implement depth calculation logic if needed
#         pass

#     def list_terms(self, prefix="GO:", include_obsolete=False):
#         return [
#             term.id
#             for term in self.queries.ont
#             if term.id.startswith(prefix) and (include_obsolete or not term.obsolete)
#         ]

#     def get_term_info(self, term_id: str):
#         term = self.queries.get_term(term_id)
#         return {
#             "id": term.id,
#             "name": term.name,
#             "definition": term.definition,
#             "synonyms": term.synonyms,
#         }

#     def search_terms(self, query: str, exact: bool = False):
#         results = []
#         for term in self.queries.ont:
#             if exact and term.name == query:
#                 results.append(term.id)
#             elif not exact and query.lower() in term.name.lower():
#                 results.append(term.id)
#         return results

#     def get_relationships(self, term_id: str):
#         term = self.queries.get_term(term_id)
#         return term.relationships

#     def get_terms_by_relation(self, relation: str):
#         terms = []
#         for term in self.queries.ont:
#             if relation in term.relationships:
#                 terms.append(term.id)
#         return terms

#     def get_common_ancestors(self, term_ids: list[str]):
#         ancestor_sets = [self.queries.ancestors(term_id) for term_id in term_ids]
#         return set.intersection(*ancestor_sets)

#     def term_exists(self, term_id: str):
#         try:
#             self.queries.get_term(term_id)
#             return True
#         except KeyError:
#             return False


def registry(cache_dir: Path = Path(DEFAULT_CACHE_DIR)) -> OntoRegistryClient:
    """Create a registry client."""
    registry_object = OntoRegistryClient(cache_dir=Path(cache_dir))
    registry_object.load_registry()
    return registry_object


def load(
    path: str = None,
    name_id: str = None,
    format: str = 'obo',
    cache_dir: Path = Path(DEFAULT_CACHE_DIR),
) -> Ontology:
    """Load an ontology from a local file or by ontology identifier and format.

    Args:
        path (str, optional): Path to a local ontology file. If provided, this file will be loaded.
        name_id (str, optional): Ontology identifier (e.g., 'go', 'chebi'). Used to fetch and load the ontology from the registry if path is not provided.
        format (str, optional): Ontology file format (e.g., 'obo', 'owl'). Defaults to 'obo'. Used only if loading by name_id.
        cache_dir (Path, optional): Directory for caching ontology files. Defaults to DEFAULT_CACHE_DIR.

    Returns:
        Ontology: The loaded ontology object.

    Raises:
        ValueError: If neither path nor name_id is provided, or if the provided path does not exist.
    """
    loader = ProntoLoaderAdapter(cache_dir=cache_dir)

    if path is not None:
        path_obj = Path(path)
        if path_obj.exists():
            return loader.load_from_file(path_file=path_obj)
        else:
            raise ValueError(f'Provided path does not exist: {path}')
    elif name_id is not None:
        return loader.load_from_registry(name_id=name_id, format=format)
    else:
        raise ValueError("Either 'path' or 'name_id' must be provided.")
