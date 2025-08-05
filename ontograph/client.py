"""Client interfaces for ontology catalog and ontology operations.

This module provides two main classes:
- ClientCatalog: For interacting with the ontology catalog, listing available ontologies, and retrieving metadata.
- ClientOntology: For loading, navigating, and querying individual ontologies.

Example:
    >>> catalog = ClientCatalog()
    >>> catalog.load_catalog()
    >>> catalog.list_available_ontologies()[0]
    {'id': 'ado', 'title': "Alzheimer's Disease Ontology"}

    >>> client = ClientOntology()
    >>> ontology = client.load(name_id="go", format="obo")
    >>> client.get_children("GO:0008150")[0]
    'GO:0002376'
"""

from pathlib import Path
from collections.abc import Iterator

from ontograph.loader import ProntoLoaderAdapter
from ontograph.models import Ontology, CatalogOntologies
from ontograph.downloader import DownloaderPort
from ontograph.config.settings import DEFAULT_CACHE_DIR
from ontograph.queries.navigator import OntologyNavigator
from ontograph.queries.relations import OntologyRelations
from ontograph.queries.introspection import OntologyIntrospection

__all__ = [
    'ClientCatalog',
    'ClientOntology',
]


class ClientCatalog:
    """Client for interacting with the ontology catalog.

    Allows loading the catalog, listing available ontologies, and retrieving metadata.

    Example:
        >>> catalog = ClientCatalog()
        >>> catalog.load_catalog()
        >>> catalog.list_available_ontologies()[0]
        {'id': 'ado', 'title': "Alzheimer's Disease Ontology"}
    """

    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR) -> None:
        """Initialize the ClientCatalog.

        Args:
            cache_dir (str, optional): Directory for caching catalog data. Defaults to DEFAULT_CACHE_DIR.
        """
        self.__catalog_adapter = CatalogOntologies(cache_dir=Path(cache_dir))

    def load_catalog(self, force_download: bool = False) -> None:
        """Load the ontology catalog.

        Args:
            force_download (bool, optional): Force download of catalog data. Defaults to False.

        Example:
            >>> catalog = ClientCatalog()
            >>> catalog.load_catalog()
        """
        return self.__catalog_adapter.load_catalog(
            force_download=force_download
        )

    def catalog_as_dict(self) -> dict:
        """Retrieve the ontology catalog as a dictionary.

        Returns:
            dict: The ontology catalog.

        Example:
            >>> catalog = ClientCatalog()
            >>> catalog.load_catalog()
            >>> isinstance(catalog.catalog_as_dict(), dict)
            True
        """
        return self.__catalog_adapter.catalog

    def list_available_ontologies(self) -> list[dict]:
        """List all available ontologies in the catalog.

        Returns:
            list[dict]: List of ontology metadata dictionaries.

        Example:
            >>> catalog = ClientCatalog()
            >>> catalog.load_catalog()
            >>> isinstance(catalog.list_available_ontologies(), list)
            True
        """
        return self.__catalog_adapter.list_available_ontologies()

    def print_available_ontologies(self) -> None:
        """Print all available ontologies in the catalog.

        Example:
            - catalog = ClientCatalog()
            - catalog.load_catalog()
            - catalog.print_available_ontologies()
        """
        return self.__catalog_adapter.print_available_ontologies()

    def print_catalog_schema_tree(self) -> None:
        """Print the schema tree of the ontology catalog.

        Example:
            - catalog = ClientCatalog()
            - catalog.print_catalog_schema_tree()
        """
        self.__catalog_adapter.print_catalog_schema_tree()

    def get_ontology_metadata(
        self, ontology_id: str, show_metadata: bool = False
    ) -> dict:
        """Retrieve metadata for a specific ontology.

        Args:
            ontology_id (str): Ontology identifier.
            show_metadata (bool, optional): Include detailed metadata. Defaults to False.

        Returns:
            dict: Metadata for the specified ontology.

        Example:
            >>> catalog = ClientCatalog()
            >>> catalog.load_catalog()
            >>> meta = catalog.get_ontology_metadata('go')
            >>> isinstance(meta, dict)
            True
        """
        return self.__catalog_adapter.get_ontology_metadata(
            ontology_id, show_metadata=show_metadata
        )

    def get_download_url(self, ontology_id: str, format: str = 'obo') -> str:
        """Retrieve the download URL for a specific ontology and format.

        Args:
            ontology_id (str): Ontology identifier.
            format (str, optional): Format (e.g., 'obo', 'json'). Defaults to 'obo'.

        Returns:
            str: Download URL.

        Example:
            >>> catalog = ClientCatalog()
            >>> catalog.load_catalog()
            >>> url = catalog.get_download_url('go')
            >>> isinstance(url, str)
            True
        """
        return self.__catalog_adapter.get_download_url(ontology_id, format)

    def get_available_formats(self, ontology_id: str) -> list[str]:
        """Retrieve available formats for a given ontology.

        Args:
            ontology_id (str): Ontology identifier.

        Returns:
            list[str]: Available formats.

        Example:
            >>> catalog = ClientCatalog()
            >>> catalog.load_catalog()
            >>> formats = catalog.get_available_formats('go')
            >>> isinstance(formats, list)
            True
        """
        return self.__catalog_adapter.get_available_formats(ontology_id)


class ClientOntology:
    """Client for loading and querying a single ontology.

    Supports loading from file, catalog, or URL, and provides navigation, relation, and introspection methods.

    Example:
        >>> client = ClientOntology()
        >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
        >>> client.get_root()
        [Term('Z', name='root')]
    """

    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR) -> None:
        """Initialize the ClientOntology.

        Args:
            cache_dir (str, optional): Directory for caching ontology data. Defaults to DEFAULT_CACHE_DIR.
        """
        self._cache_dir = Path(cache_dir)
        self._ontology: Ontology | None = None
        self._navigator = None
        self._relations = None
        self._introspection = None

    def load(
        self,
        file_path_ontology: str | None = None,
        name_id: str | None = None,
        format: str | None = None,
        url_ontology: str | None = None,
        filename: str | None = None,
        downloader: DownloaderPort = None,
    ) -> Ontology:
        """Load an ontology using one of three strategies.

        Exactly one of the following must be provided:
            - file_path_ontology
            - name_id and format
            - url_ontology, filename, and downloader

        Args:
            file_path_ontology (str, optional): Path to local ontology file.
            name_id (str, optional): Catalog ontology ID.
            format (str, optional): Format for catalog loading.
            url_ontology (str, optional): Remote ontology URL.
            filename (str, optional): Filename for downloaded ontology.
            downloader (callable, optional): Downloader function.

        Returns:
            Ontology: Loaded ontology.

        Raises:
            ValueError: If no or multiple strategies are provided.
            RuntimeError: If loading fails.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> isinstance(ontology, Ontology)
            True
        """
        is_file = bool(file_path_ontology)
        is_catalog = bool(name_id and format)
        is_url = bool(url_ontology and filename and downloader)

        strategies = {
            'file': is_file,
            'catalog': is_catalog,
            'url': is_url,
        }
        active_strategies = [key for key, value in strategies.items() if value]

        if len(active_strategies) == 0:
            raise ValueError('No valid loading strategy provided.')
        if len(active_strategies) > 1:
            raise ValueError(
                f'Multiple loading strategies provided: {active_strategies}. Please specify only one.'
            )

        loader = ProntoLoaderAdapter(cache_dir=self._cache_dir)

        if is_file:
            self._ontology = loader.load_from_file(file_path_ontology)
        elif is_catalog:
            self._ontology = loader.load_from_catalog(name_id, format)
        elif is_url:
            self._ontology = loader.load_from_url(
                url_ontology, filename, downloader
            )
        else:
            raise RuntimeError(
                'Unexpected loading strategy resolution failure.'
            )

        self._initialize_queries()

        return self._ontology

    def _initialize_queries(self) -> None:
        """Initialize query adapters for navigation, relations, and introspection."""
        self._navigator = OntologyNavigator(self._get_ontology)
        self._relations = OntologyRelations(navigator=self._navigator)
        self._introspection = OntologyIntrospection(
            navigator=self._navigator,
            relations=self._relations,
        )

    @property
    def _get_ontology(self) -> Ontology:
        """Access the loaded ontology.

        Returns:
            Ontology: The loaded ontology.

        Raises:
            RuntimeError: If ontology not loaded.

        """
        if self._ontology is None:
            raise RuntimeError('Ontology not loaded. Call `load()` first.')
        return self._ontology

    # ---- Navigation Methods

    def get_term(self, term_id: str) -> object:
        """Retrieve a term by its ID.

        Args:
            term_id (str): Term identifier.

        Returns:
            object: Term object.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> client.get_term("A")
            Term('A', name='termA')
        """
        return self._navigator.get_term(term_id=term_id)

    def get_parents(self, term_id: str, include_self: bool = False) -> list:
        """Get parent terms of a given term.

        Args:
            term_id (str): Term identifier.
            include_self (bool, optional): Include the term itself. Defaults to False.

        Returns:
            list: Parent term IDs.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> client.get_parents("D")
            ['A']
        """
        return self._navigator.get_parents(
            term_id=term_id, include_self=include_self
        )

    def get_children(self, term_id: str, include_self: bool = False) -> list:
        """Get child terms of a given term.

        Args:
            term_id (str): Term identifier.
            include_self (bool, optional): Include the term itself. Defaults to False.

        Returns:
            list: Child term IDs.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> client.get_children("D")
            ['E', 'F', 'G']
        """
        return self._navigator.get_children(
            term_id=term_id, include_self=include_self
        )

    def get_ancestors(
        self,
        term_id: str,
        distance: int | None = None,
        include_self: bool = False,
    ) -> list[str]:
        """Get ancestor terms of a given term.

        Args:
            term_id (str): Term identifier.
            distance (int, optional): Maximum distance from term. Defaults to None.
            include_self (bool, optional): Include the term itself. Defaults to False.

        Returns:
            list[str]: Ancestor term IDs.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> client.get_ancestors("D")
            ['A', 'Z']
        """
        return self._navigator.get_ancestors(
            term_id=term_id,
            distance=distance,
            include_self=include_self,
        )

    def get_ancestors_with_distance(
        self, term_id: str, include_self: bool = False
    ) -> Iterator[tuple[object, int]]:
        """Get ancestor terms and their distances.

        Args:
            term_id (str): Term identifier.
            include_self (bool, optional): Include the term itself. Defaults to False.

        Returns:
            Iterator[tuple[object, int]]: Iterator of (term, distance).

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> list(client.get_ancestors_with_distance("D"))
            [(Term('A', name='termA'), -1), (Term('Z', name='root'), -2)]
        """
        return self._navigator.get_ancestors_with_distance(
            term_id=term_id,
            include_self=include_self,
        )

    def get_descendants(
        self,
        term_id: str,
        distance: int | None = None,
        include_self: bool = False,
    ) -> set[str]:
        """Get descendant terms of a given term.

        Args:
            term_id (str): Term identifier.
            distance (int, optional): Maximum distance from term. Defaults to None.
            include_self (bool, optional): Include the term itself. Defaults to False.

        Returns:
            set[str]: Descendant term IDs.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> sorted(client.get_descendants("F"))
            ['O', 'Y']
        """
        return self._navigator.get_descendants(
            term_id=term_id,
            distance=distance,
            include_self=include_self,
        )

    def get_descendants_with_distance(
        self, term_id: str, include_self: bool = False
    ) -> Iterator[tuple[object, int]]:
        """Get descendant terms and their distances.

        Args:
            term_id (str): Term identifier.
            include_self (bool, optional): Include the term itself. Defaults to False.

        Returns:
            Iterator[tuple[object, int]]: Iterator of (term, distance).

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> list(client.get_descendants_with_distance("F"))
            [(Term('O', name='termO'), 1), (Term('Y', name='termY'), 1)]
        """
        return self._navigator.get_descendants_with_distance(
            term_id=term_id,
            include_self=include_self,
        )

    def get_siblings(
        self, term_id: str, include_self: bool = False
    ) -> set[str]:
        """Get sibling terms of a given term.

        Args:
            term_id (str): Term identifier.
            include_self (bool, optional): Include the term itself. Defaults to False.

        Returns:
            set[str]: Sibling term IDs.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> sorted(client.get_siblings("F"))
            ['E', 'G']

        """
        return self._navigator.get_siblings(
            term_id=term_id, include_self=include_self
        )

    def get_root(self) -> list:
        """Get root terms of the ontology.

        Returns:
            list: Root term IDs.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> client.get_root()
            [Term('Z', name='root')]
        """
        return self._navigator.get_root()

    # ---- Relation Methods

    def is_ancestor(self, ancestor_node: str, descendant_node: str) -> bool:
        """Check if one term is an ancestor of another.

        Args:
            ancestor_node (str): Ancestor term ID.
            descendant_node (str): Descendant term ID.

        Returns:
            bool: True if ancestor_node is ancestor of descendant_node.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> client.is_ancestor("A", "N")
            True
        """
        return self._relations.is_ancestor(
            ancestor_node=ancestor_node,
            descendant_node=descendant_node,
        )

    def is_descendant(self, descendant_node: str, ancestor_node: str) -> bool:
        """Check if one term is a descendant of another.

        Args:
            descendant_node (str): Descendant term ID.
            ancestor_node (str): Ancestor term ID.

        Returns:
            bool: True if descendant_node is descendant of ancestor_node.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> client.is_descendant("N", "A")
            True
        """
        return self._relations.is_descendant(
            descendant_node=descendant_node,
            ancestor_node=ancestor_node,
        )

    def is_sibling(self, node_a: str, node_b: str) -> bool:
        """Check if two terms are siblings.

        Args:
            node_a (str): First term ID.
            node_b (str): Second term ID.

        Returns:
            bool: True if node_a and node_b are siblings.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> client.is_sibling("E", "F")
            True
        """
        return self._relations.is_sibling(node_a=node_a, node_b=node_b)

    def get_common_ancestors(self, node_ids: list[str]) -> set:
        """Get common ancestors of multiple terms.

        Args:
            node_ids (list[str]): List of term IDs.

        Returns:
            set: Common ancestor term IDs.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> sorted(client.get_common_ancestors(["K", "L"]))
            ['B', 'Z']
        """
        return self._relations.get_common_ancestors(node_ids=node_ids)

    def get_lowest_common_ancestors(self, node_ids: list[str]) -> set:
        """Get lowest common ancestors of multiple terms.

        Args:
            node_ids (list[str]): List of term IDs.

        Returns:
            set: Lowest common ancestor term IDs.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> client.get_lowest_common_ancestors(["K", "L"])
            {'B'}
        """
        return self._relations.get_lowest_common_ancestors(node_ids=node_ids)

    # ---- Introspection Methods

    def get_distance_from_root(self, term_id: str) -> int | None:
        """Get the distance of a term from the root.

        Args:
            term_id (str): Term identifier.

        Returns:
            int | None: Distance from root, or None if not found.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> client.get_distance_from_root("U")
            6
        """
        return self._introspection.get_distance_from_root(term_id=term_id)

    def get_path_between(self, node_a: str, node_b: str) -> list[dict]:
        """Get the path between two terms.

        Args:
            node_a (str): Start term ID.
            node_b (str): End term ID.

        Returns:
            list[dict]: List of path steps.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> client.get_path_between("N", "D")
            [{'id': 'D', 'distance': 0}, {'id': 'E', 'distance': 1}, {'id': 'N', 'distance': 2}]
            >>> client.get_path_between("N", "C")
            []
        """
        return self._introspection.get_path_between(
            node_a=node_a, node_b=node_b
        )

    def get_trajectories_from_root(self, term_id: str) -> list[dict]:
        """Get all trajectories from the root to a term.

        Args:
            term_id (str): Term identifier.

        Returns:
            list[dict]: List of trajectories.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> client.get_trajectories_from_root("A")
            [[{'id': 'Z', 'name': 'root', 'distance': -1}, {'id': 'A', 'name': 'termA', 'distance': 0}]]
        """
        return self._introspection.get_trajectories_from_root(term_id=term_id)

    def print_term_trajectories_tree(self, trajectories: list[dict]) -> None:
        """Print a tree representation of term trajectories.

        Args:
            trajectories (list[dict]): List of trajectories.

        Example:
            >>> client = ClientOntology()
            >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
            >>> traj = client.get_trajectories_from_root("D")
            >>> client.print_term_trajectories_tree(traj)
            Z: root (distance=-2)
            └── A: termA (distance=-1)
                └── D: termD (distance=0)
        """
        self._introspection.print_term_trajectories_tree(
            trajectories=trajectories
        )

        return None
