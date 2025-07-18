from pathlib import Path

from ontograph.config.settings import DEFAULT_CACHE_DIR
from ontograph.ontology_registry import OBORegistryAdapter

__all__ = [
    'OntoRegistryClient',
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


# def load(path: str, name_id: str, format: str = "obo") -> OntologyClient:
#     """Load an ontology and return a client for interacting with it."""
#     loader = ProntoLoaderAdapter(cache_dir=Path(path))
#     ontology = loader.load(name_id=name_id, format=format)
#     return OntologyClient(ontology)


# # TODO: create a client interface class to ontograph

# class OntologyClient:
#     ontology_object: Ontology

#     # 1. list of catalog of ontologies
#     # TODO: Implement a funtion that returns all the ontologies in the catalog (OBO Foundries)
#     def list_ontologies():
#         pass

#     # 2. load an ontology
#     # TODO: Implement a function to load a specified ontology in a given format.
#     # This function should accept a target path to download the ontology or retrieve
#     # it from cache if already available.
#     def load(path: str, name_id: str, format: str = "obo") -> Any:
#         pass

#     # ----------------------------------------------
#     # ----      Core hierarchical queries       ----
#     # ----------------------------------------------
#     # 3. get parents/ancestors
#     # TODO: Implement a function to return all parent terms of a given ontology term,
#     # allowing control over the traversal depth.
#     def get_parents(
#         term_id: str, depth: int = -1, include_self: bool = False
#     ) -> list[str]:
#         pass

#     # 4. get children/descendants
#     # TODO: Implement a function to retrieve all child terms of a given ontology term,
#     # with optional control over traversal depth.
#     def get_children(
#         term_id: str, depth: int = -1, include_self: bool = False
#     ) -> list[str]:
#         pass

#     # 5. get siblings
#     # TODO: retrieve term sharing the same parents(s)
#     def get_siblings(term_id):
#         pass

#     # 6. get root terms
#     # TODO: Retrieve all terms without parents (top categories in our ontology)
#     def get_roots():
#         pass

#     # 7. get leaf terms
#     # TODO: retrieve all terms without children (e.g., most specific categories)
#     def get_leaves():
#         pass

#     # ----------------------------------------------
#     # ----        Graph & Path queries          ----
#     # ----------------------------------------------
#     # 8. find path between two terms
#     # TODO: determine the relationship?path between two terms (if any)
#     def find_path(source_id, target_id):
#         pass

#     # 9. Check subsumption (is a relationship)
#     # TODO: Check if a term is descendant of another
#     def is_descendant(child_id, parent_id):
#         pass

#     # 10. get_depth(term_id)
#     # TODO: return the depth of a term in the hierarchy
#     def get_depth(term_id):
#         pass

#     # ----------------------------------------------
#     # ----      Ontology Metadata queries       ----
#     # ----------------------------------------------
#     # 11. List of terms
#     # TODO: Enumerate all terms with optional filtering
#     # TODO: clarify function
#     def list_terms(prefix="GO:", include_obsolete=False):
#         pass

#     # 12. get term metadata
#     # TODO: retrieve details such as label, definition, synonyms, etc.
#     def get_term_info(term_id):
#         pass

#     # 12. Search terms by label or synonym
#     # TODO: Fuzzy or exact search for term labels.
#     # TODO: clarify this function
#     def search_terms(query="metabolic process", exact=False):
#         pass

#     # ----------------------------------------------
#     # ----      Advanced semantic  queries      ----
#     # ----------------------------------------------
#     # 13. get relationships of a term
#     # TODO: Return all relationships (not just hierarchical: part_of, regulates, etc.).
#     # TODO: clarify
#     def get_relationships(term_id):
#         pass

#     # 14. Get terms by relationship type
#     # TODO: Retrieve all terms linked via a specific relationship type.
#     def get_terms_by_relation(terms="part_of"):
#         pass

#     # 15. Find common ancestors
#     # TODO: Determine shared parent terms between two or more terms.
#     def get_common_ancestors(term_ids):
#         pass

#     # ----------------------------------------------
#     # ----              Utilities               ----
#     # ----------------------------------------------
#     # 16. Check if term exists
#     # TODO: Validate a term ID
#     def term_exists(term_id):
#         pass
