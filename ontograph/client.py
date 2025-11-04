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

import re
import logging
from pathlib import Path
from collections.abc import Iterator

from ontograph.loader import ProntoLoaderAdapter
from ontograph.models import (
    Graph,
    Ontology,
    TermList,
    LookUpTables,
    NodeContainer,
    EdgesContainer,
    EdgesDataframe,
    NodesDataframe,
    CatalogOntologies,
)
from ontograph.downloader import DownloaderPort
from ontograph.config.settings import DEFAULT_CACHE_DIR
from ontograph.queries.navigator import (
    NavigatorPronto,
    NavigatorGraphblas,
)
from ontograph.queries.relations import (
    RelationsPronto,
    RelationsGraphblas,
)
from ontograph.utils.pronto_utils import extract_terms
from ontograph.queries.introspection import (
    IntrospectionPronto,
    IntrospectionGraphblas,
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

__all__ = [
    'ClientCatalog',
    'ClientOntology',
]


# --------------------------------------------- #
# ----          Client for Catalog          --- #
# --------------------------------------------- #
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


# --------------------------------------------- #
# ----          Client for Ontology         --- #
# --------------------------------------------- #
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
        self._ontology = None
        self._lookup_tables = None
        self._navigator = None
        self._relations = None
        self._introspection = None

    def __create_graphblas_ontology(
        self, ontology: Ontology, include_obsolete: bool = False
    ) -> tuple[LookUpTables, Graph]:
        terms = extract_terms(
            ontology=ontology, include_obsolete=include_obsolete
        )

        # Step 2. Extract Lookup Tables and DataFrames
        lookup_tables = LookUpTables(terms=terms)

        # Step 3. Create Nodes objects
        # Step 3.1. Create Nodes DataFrame
        nodes_df = NodesDataframe(
            terms=terms, include_obsolete=include_obsolete
        )
        # Step 3.2. Create Nodes Indexes
        nodes_indexes = NodeContainer(
            nodes_indices=nodes_df.get_dataframe()['index'].to_numpy(dtype=int)
        )

        # Step 4. Create Edges objects
        # Step 4.1. Create Edges DataFrame
        edges_df = EdgesDataframe(
            terms=terms, include_obsolete=include_obsolete
        )
        # Step 4.2. Create Edges Indexes
        edges_indexes = EdgesContainer(terms=terms, lookup_tables=lookup_tables)

        # Step 5. Create Graph object
        graph = Graph(
            nodes_indexes=nodes_indexes,
            nodes_dataframe=nodes_df,
            edges_indexes=edges_indexes,
            edges_dataframe=edges_df,
            lookup_tables=lookup_tables,
        )

        return lookup_tables, graph

    def _detect_source_type(self, source: str) -> str:
        """Detect the type of ontology source: file path, OBO Foundry ID, or URL.

        This method checks the input string and determines its type in the following priority order:
        1. Local file path
        2. OBO Foundry identifier (alphanumeric, underscore, or hyphen; no slashes or dots)
        3. HTTP/HTTPS URL

        Args:
            source (str): The ontology source string to check. Can be a file path, OBO Foundry ID, or URL.

        Returns:
            str: The detected source type. One of 'file', 'obo', or 'url'.

        Raises:
            ValueError: If the source type cannot be determined.

        Example:
            >>> client = ClientOntology()
            >>> client._detect_source_type("./ontology.obo")
            'file'
            >>> client._detect_source_type("go")
            'obo'
            >>> client._detect_source_type("https://example.com/ontology.obo")
            'url'
        """
        path = Path(source)

        # 1. File path takes highest priority
        if path.exists() and path.is_file():
            return 'file'

        # 2. OBO Foundry ontology name (simple identifier, no slashes or dots)
        if re.fullmatch(r'[A-Za-z0-9_-]+', source):
            return 'obo'

        # 3. URL (fallback)
        if re.match(r'^https?://', source):
            return 'url'

        raise ValueError(f"Cannot determine ontology source type: '{source}'")

    def load(
        self,
        source: str,
        downloader: DownloaderPort = None,
        include_obsolete: bool = False,
        backend: str = 'pronto',
    ) -> None:
        """Load an ontology from a file path, URL, or OBO Foundry catalog.

        This method detects the source type and loads the ontology using the appropriate strategy:
        - Local file path
        - URL
        - OBO Foundry catalog identifier

        It also initializes query adapters for navigation, relations, and introspection based on the selected backend.

        Args:
            source (str): Path to the ontology file, URL, or OBO Foundry identifier.
            downloader (DownloaderPort, optional): Downloader adapter for remote files. Defaults to None.
            include_obsolete (bool, optional): If True, include obsolete terms when building GraphBLAS structures. Defaults to False.
            backend (str, optional): Backend for queries ('pronto' or 'graphblas'). Defaults to 'pronto'.

        Raises:
            FileNotFoundError: If the ontology source cannot be found as a file, URL, or catalog entry.
            ValueError: If an unknown backend is specified.

        Returns:
            None

        Example:
            >>> client = ClientOntology()
            >>> client.load(source="./tests/resources/dummy_ontology.obo")
        """
        logger.info(f'Loading ontology from source: {source} ...')
        loader = ProntoLoaderAdapter(cache_dir=self._cache_dir)

        path = Path(source)
        ontology = None

        # 1. Case 1: Local file exists
        if path.exists():
            logger.info(
                f'Found local file at {path}, loading with ProntoLoaderAdapter...'
            )
            ontology = loader.load_from_file(file_path_ontology=path)

        # 2. Case 2: Provided source is a URL
        elif re.match(r'^https?://', source):
            logger.info(
                f'Detected URL source, downloading ontology from {source}'
            )
            filename = Path(source).name or 'ontology.obo'
            ontology = loader.load_from_url(source, filename, downloader)

        # 3. Case 3: Try OBO catalog (if file missing or simple ID)
        else:
            catalog_client = ClientCatalog(cache_dir=self._cache_dir)
            catalog_client.load_catalog()
            available = [
                o['id'] for o in catalog_client.list_available_ontologies()
            ]
            name_id = Path(source).stem.lower()

            if name_id in available:
                logger.info(
                    f"Ontology '{name_id}' found in catalog, downloading..."
                )
                ontology = loader.load_from_catalog(
                    name_id=name_id, format='obo'
                )
            else:
                msg = f"Ontology '{source}' not found as file, URL, or catalog entry."
                logger.error(msg)
                raise FileNotFoundError(msg)

        # 4. Graph backend construction
        logger.info(f'Using backend: {backend}')
        if backend == 'pronto':
            self._ontology = ontology
            self._lookup_tables = None

        elif backend == 'graphblas':
            self._lookup_tables, self._ontology = (
                self.__create_graphblas_ontology(
                    ontology=ontology.get_ontology(),
                    include_obsolete=include_obsolete,
                )
            )
        else:
            raise ValueError(f'Unknown backend specified: {backend}')

        # Initialize queries
        logger.info('Initialize queries sequence.')
        self._initialize_queries(backend)

        logger.info('Ontology loading complete.')

    def _initialize_queries(self, backend: str) -> None:
        """Initializes query adapters for navigation, relations, and introspection based on the specified backend.

        Args:
            backend (str): The backend to use for query adapters. Supported values are 'pronto' and 'graphblas'.

        Raises:
            KeyError: If the specified backend is not supported.

        """

        if backend == 'pronto':
            self._navigator = NavigatorPronto(ontology=self._get_ontology)
            self._relations = RelationsPronto(navigator=self._navigator)
            self._introspection = IntrospectionPronto(
                navigator=self._navigator,
                relations=self._relations,
            )
        elif backend == 'graphblas':
            self._navigator = NavigatorGraphblas(
                ontology=self._get_ontology, lookup_tables=self._lookup_tables
            )
            self._relations = RelationsGraphblas(
                navigator=self._navigator, lookup_tables=self._lookup_tables
            )
            self._introspection = IntrospectionGraphblas(
                navigator=self._navigator,
                relations=self._relations,
                lookup_tables=self._lookup_tables,
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
    # def get_term(self, term_id: str) -> object:
    #     """Retrieve a term by its ID.

    #     Args:
    #         term_id (str): Term identifier.

    #     Returns:
    #         object: Term object.

    #     Example:
    #         >>> client = ClientOntology()
    #         >>> ontology = client.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
    #         >>> client.get_term("A")
    #         Term('A', name='termA')
    #     """
    #     return self._navigator.get_term(term_id=term_id)

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
        term_ids = self._navigator.get_parents(
            term_id=term_id, include_self=include_self
        )
        return TermList(term_ids, self._lookup_tables)
        # return self._navigator.get_parents(
        #     term_id=term_id, include_self=include_self
        # )

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
        term_ids = self._navigator.get_children(
            term_id=term_id, include_self=include_self
        )
        return TermList(term_ids, self._lookup_tables)

        # return self._navigator.get_children(
        #     term_id=term_id, include_self=include_self
        # )

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
        term_ids = self._navigator.get_ancestors(
            term_id=term_id,
            distance=distance,
            include_self=include_self,
        )
        return TermList(term_ids, self._lookup_tables)
        # return self._navigator.get_ancestors(
        #     term_id=term_id,
        #     distance=distance,
        #     include_self=include_self,
        # )

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
        term_ids = self._navigator.get_descendants(
            term_id=term_id,
            distance=distance,
            include_self=include_self,
        )
        return TermList(term_ids, self._lookup_tables)
        # return self._navigator.get_descendants(
        #     term_id=term_id,
        #     distance=distance,
        #     include_self=include_self,
        # )

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
        term_ids = self._navigator.get_siblings(
            term_id=term_id, include_self=include_self
        )
        return TermList(term_ids, self._lookup_tables)
        # return self._navigator.get_siblings(
        #     term_id=term_id, include_self=include_self
        # )

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
        term_ids = self._navigator.get_root()
        return TermList(term_ids, self._lookup_tables)
        # return self._navigator.get_root()

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
        term_ids = self._relations.get_common_ancestors(node_ids=node_ids)
        return TermList(term_ids, self._lookup_tables)
        # return self._relations.get_common_ancestors(node_ids=node_ids)

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
        term_ids = self._relations.get_lowest_common_ancestors(
            node_ids=node_ids
        )
        return TermList(term_ids, self._lookup_tables)
        # return self._relations.get_lowest_common_ancestors(node_ids=node_ids)

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
