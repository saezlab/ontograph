from abc import ABC, abstractmethod
import logging
from collections import deque
from collections.abc import Iterator

import numpy as np
import graphblas as gb

from ontograph.models import Ontology, LookUpTables

__all__ = [
    'NavigatorOntology',
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# --------------------------------------------------------
# ----     OntologyNavigator Port (abstract class)    ----
# --------------------------------------------------------
class NavigatorOntology(ABC):
    """Abstract navigator for traversing and querying ontology term relationships."""

    def __init__(self, ontology: 'Ontology') -> None:
        self._ontology = ontology.get_ontology()

    @abstractmethod
    def get_term(self, term_id: str) -> object:
        """Retrieve the ontology term object for a given term ID."""
        pass

    @abstractmethod
    def get_parents(self, term_id: str, include_self: bool = False) -> list:
        """Retrieve the parent term IDs (superclasses) of a given term."""
        pass

    @abstractmethod
    def get_children(self, term_id: str, include_self: bool = False) -> list:
        """Retrieve the child term IDs (subclasses) of a given term."""
        pass

    @abstractmethod
    def get_ancestors(
        self,
        term_id: str,
        distance: int | None = None,
        include_self: bool = False,
    ) -> list[str]:
        """Retrieve all ancestor term IDs (superclasses) of a given term."""
        pass

    @abstractmethod
    def get_ancestors_with_distance(
        self, term_id: str, include_self: bool = False
    ) -> 'Iterator[tuple[object, int]]':
        """Retrieve all ancestor terms with their distance from the given term."""
        pass

    @abstractmethod
    def get_descendants(
        self,
        term_id: str,
        distance: int | None = None,
        include_self: bool = False,
    ) -> set[str]:
        """Retrieve all descendant term IDs (subclasses) of a given term."""
        pass

    @abstractmethod
    def get_descendants_with_distance(
        self, term_id: str, include_self: bool = False
    ) -> 'Iterator[tuple[object, int]]':
        """Retrieve all descendant terms with their distance from the given term."""
        pass

    @abstractmethod
    def get_siblings(
        self, term_id: str, include_self: bool = False
    ) -> set[str]:
        """Retrieve the sibling term IDs of a given term."""
        pass

    @abstractmethod
    def get_root(self) -> list:
        """Returns the root term(s) of the ontology — terms with no superclasses."""
        pass


# ---------------------------------------------------------
# ----     NavigatorPronto adapter (concrete class)    ----
# ---------------------------------------------------------
class NavigatorPronto(NavigatorOntology):
    """Navigator for traversing and querying ontology term relationships.

    This class provides methods to retrieve parent, ancestor, descendant, sibling, and root terms
    from an ontology loaded via the Ontology model. It is designed to facilitate graph-like navigation
    of ontology structures, supporting queries for hierarchical relationships.

    Attributes:
        __ontology: The underlying ontology object.
    """

    def __init__(self, ontology: Ontology) -> None:
        """Initializes the OntologyNavigator.

        Args:
            ontology (Ontology): An Ontology object containing the loaded ontology data.
        """
        self.__ontology = ontology.get_ontology()

    def get_term(self, term_id: str) -> object:
        """Retrieves the ontology term object for a given term ID.

        Args:
            term_id (str): The identifier of the ontology term.

        Returns:
            pronto.Term: The ontology term object corresponding to the given ID.

        Raises:
            KeyError: If the term_id is not found in the ontology.
        """
        try:
            return self.__ontology[term_id]
        except KeyError:
            logger.exception(f"Term ID '{term_id}' not found in ontology.")
            raise

    def get_parents(self, term_id: str, include_self: bool = False) -> list:
        """Retrieves the parent term IDs (superclasses) of a given term.

        Args:
            term_id (str): The identifier of the term whose parents are to be retrieved.
            include_self (bool, optional): If True, include the term itself in the result. Defaults to False.

        Returns:
            list: A list of parent term IDs.
        """
        try:
            term = self.get_term(term_id)
        except KeyError:
            logger.exception(f"Term ID '{term_id}' not found in ontology.")
            return []

        try:
            parents = [
                parent.id
                for parent in term.superclasses(
                    distance=1, with_self=include_self
                )
            ]
            logger.debug(f'parents: {parents}')
            return parents
        except Exception as e:
            logger.exception(
                f"Error retrieving parents for term '{term_id}': {e}"
            )
            return []

    def get_children(self, term_id: str, include_self: bool = False) -> list:
        """Retrieves the child term IDs (subclasses) of a given term.

        Args:
            term_id (str): The identifier of the term whose children are to be retrieved.
            include_self (bool, optional): If True, include the term itself in the result. Defaults to False.

        Returns:
            list: A list of child term IDs.

        Raises:
            KeyError: If the term_id is not found in the ontology.
        """
        try:
            term = self.get_term(term_id)
        except KeyError:
            logger.exception(f"Term ID '{term_id}' not found in ontology.")
            return []

        try:
            children = [
                child.id
                for child in term.subclasses(distance=1, with_self=include_self)
            ]
            logger.debug(f'children: {children}')
            return children
        except Exception as e:
            logger.exception(
                f"Error retrieving children for term '{term_id}': {e}"
            )
            return []

    def get_ancestors(
        self,
        term_id: str,
        distance: int | None = None,
        include_self: bool = False,
    ) -> list[str]:
        """Retrieve all ancestor term IDs (superclasses) of a given term.

        Args:
            term_id (str): The identifier of the term whose ancestors are to be retrieved.
            distance (int | None, optional): The maximum distance to traverse up the hierarchy. If None, retrieves all ancestors. Defaults to None.
            include_self (bool, optional): If True, include the term itself in the result. Defaults to False.

        Returns:
            set[str]: A list of ancestor term IDs. None in case of having no ancestors.

        Raises:
            KeyError: If the term_id is not found in the ontology.
            Exception: If an error occurs during ancestor retrieval.
        """
        try:
            term = self.get_term(term_id)
        except KeyError:
            logger.exception(f"Term ID '{term_id}' not found in ontology.")
            return []

        try:
            ancestor_terms = term.superclasses(
                distance=distance, with_self=include_self
            )
            ancestor_ids = [ancestor.id for ancestor in ancestor_terms]
            logger.debug(f"Ancestors of term '{term_id}': {ancestor_ids}")
            return ancestor_ids
        except Exception as e:
            logger.exception(
                f"Error retrieving ancestors for term '{term_id}': {e}"
            )
            return []

    def get_ancestors_with_distance(
        self, term_id: str, include_self: bool = False
    ) -> Iterator[tuple[object, int]]:
        """Retrieve all ancestor terms with their distance from the given term.

        Args:
            term_id (str): The identifier of the ontology term.
            include_self (bool): Whether to include the term itself at distance 0.

        Returns:
            Iterator(tuple[Term, int]): Pairs of ancestor term objects and their distance (negative integer).

        Raises:
            KeyError: If the term is not found in the ontology.
        """

        try:
            term = self.get_term(term_id)
        except KeyError:
            logger.exception(f"Term ID '{term_id}' not found in ontology.")
            return iter(())

        visited = set()
        queue = deque()

        if include_self:
            queue.append((term, 0))
        else:
            for parent in term.superclasses(distance=1):
                if parent.id != term.id:
                    queue.append((parent, -1))

        while queue:
            current_term, dist = queue.popleft()
            if current_term.id in visited:
                continue

            visited.add(current_term.id)
            yield current_term, dist

            for parent in current_term.superclasses(distance=1):
                if parent.id not in visited and parent.id != current_term.id:
                    queue.append((parent, dist - 1))

    def get_descendants(
        self,
        term_id: str,
        distance: int | None = None,
        include_self: bool = False,
    ) -> set[str]:
        """Retrieve all descendant term IDs (subclasses) of a given term.

        Args:
            term_id (str): The identifier of the term whose descendants are to be retrieved.
            distance (int | None, optional): The maximum distance to traverse down the hierarchy. If None, retrieves all descendants. Defaults to None.
            include_self (bool, optional): If True, include the term itself in the result. Defaults to False.

        Returns:
            set[str]: A set of descendant term IDs.

        Raises:
            KeyError: If the term_id is not found in the ontology.
            Exception: If an error occurs during descendant retrieval.
        """
        try:
            term = self.get_term(term_id)
        except KeyError:
            logger.exception(f"Term ID '{term_id}' not found in ontology.")
            return set()

        try:
            descendant_ids = {
                descendant.id
                for descendant in term.subclasses(distance=distance)
            }
            if not include_self and term.id in descendant_ids:
                descendant_ids.remove(term.id)
            logger.debug(f"Descendants of term '{term_id}': {descendant_ids}")
            return descendant_ids
        except Exception as e:
            logger.exception(
                f"Error retrieving descendants for term '{term_id}': {e}"
            )
            return set()

    def get_descendants_with_distance(
        self, term_id: str, include_self: bool = False
    ) -> Iterator[tuple[object, int]]:
        """Retrieve all descendant terms with their distance from the given term.

        Args:
            term_id (str): The identifier of the ontology term.
            include_self (bool): Whether to include the term itself at distance 0.

        Returns:
            Iterator[tuple[Term, int]]: Generator of (descendant term, distance) pairs. Distance in positive numbers.

        Raises:
            KeyError: If the term ID is not found in the ontology.
        """
        try:
            term = self.get_term(term_id)
        except KeyError:
            logger.exception(f"Term ID '{term_id}' not found in ontology.")
            return iter(())

        visited = set()
        queue = deque()

        if include_self:
            queue.append((term, 0))
        else:
            for child in term.subclasses(distance=1):
                if child.id != term.id:
                    queue.append((child, 1))

        while queue:
            current_term, dist = queue.popleft()
            if current_term.id in visited:
                continue

            visited.add(current_term.id)
            yield current_term, dist

            for child in current_term.subclasses(distance=1):
                if child.id not in visited and child.id != current_term.id:
                    queue.append((child, dist + 1))

    def get_siblings(
        self, term_id: str, include_self: bool = False
    ) -> set[str]:
        """Retrieve the sibling term IDs of a given term.

        Siblings are terms that share at least one direct parent (superclass) with the given term.

        Args:
            term_id (str): The identifier of the ontology term.
            include_self (bool): Whether to include the term itself in the result.

        Returns:
            set[str]: A set of sibling term IDs.

        Raises:
            KeyError: If the term_id is not found in the ontology.
            Exception: If an error occurs during sibling retrieval.
        """
        logger.debug(f'Siblings for term: {term_id}')

        try:
            term = self.get_term(term_id)
        except KeyError:
            logger.exception(f"Term ID '{term_id}' not found in ontology.")
            return set()

        siblings = set()
        try:
            for parent in term.superclasses(distance=1, with_self=False):
                logger.debug(f'parent: {parent.id}')
                for child in parent.subclasses(distance=1, with_self=False):
                    logger.debug(f'child found: {child.id}')
                    siblings.add(child.id)

            if not include_self and term_id in siblings:
                siblings.remove(term_id)

            return siblings
        except Exception as e:
            logger.exception(
                f"Error retrieving siblings for term '{term_id}': {e}"
            )
            return set()

    def get_root(self) -> list:
        """Returns the root term(s) of the ontology — terms with no superclasses.

        Returns:
            list: A list of root term objects.

        Raises:
            Exception: If an error occurs during root term retrieval.
        """
        try:
            root_terms = []

            for term in self.__ontology.terms():
                if (
                    not term.obsolete
                    and len(
                        list(term.superclasses(distance=1, with_self=False))
                    )
                    == 0
                ):
                    root_terms.append(term)
            return root_terms
        except Exception as e:
            logger.exception(f'Error retrieving root terms: {e}')
            return []


# ------------------------------------------------------------
# ----     NavigatorGraphblas adapter (concrete class)    ----
# ------------------------------------------------------------
class NavigatorGraphblas(NavigatorOntology):
    def __init__(self, ontology: Ontology, lookup_tables: LookUpTables) -> None:
        self.__ontology = ontology

        # --- Nodes ---
        self.nodes_indexes = self.__ontology.nodes_indexes
        self.nodes_dataframe = self.__ontology.nodes_dataframe
        # --- Edges ---
        self.edges_indexes = self.__ontology.edges_indexes
        self.edges_dataframe = self.__ontology.edges_dataframe

        # --- Lookup Tables ---
        self.lookup_tables = lookup_tables
        self.number_nodes = self.__ontology.number_nodes
        self.number_edges = self.__ontology.number_edges

        self.matrices_container = self.__ontology.matrices_container

    def one_hot_vector(self, index: int) -> gb.Vector:
        return gb.Vector.from_coo(
            [index], [1], size=self.number_nodes, dtype=int
        )

    def _traverse_graph(
        self,
        term_id: str,
        adjacency_matrix: gb.Matrix,
        distance: int = None,
        include_self: bool = False,
    ) -> list:
        """Generalized function to traverse a graph in either direction.

        Parameters
        ----------
        term_id : str
            The starting term ID.
        adjacency_matrix : gb.Matrix
            Adjacency matrix to traverse (forward for descendants, transposed for ancestors).
        distance : int or None
            Maximum distance to traverse. None means unlimited.
        include_self : bool
            Whether to include the starting node in the result.

        Returns:
        -------
        List[str]
            List of term IDs reached.
        """
        if term_id not in self.lookup_tables.get_lut_term_to_index():
            raise KeyError(f'Unknown term ID: {term_id}')

        index = self.lookup_tables.term_to_index(term_id)
        current_vector = self.one_hot_vector(index=index)
        visited = set()

        if include_self:
            visited.add(index)

        while current_vector.nvals != 0 and distance != 0:
            next_vector = gb.Vector(dtype=int, size=adjacency_matrix.nrows)
            next_vector << gb.semiring.plus_times(
                adjacency_matrix @ current_vector
            )  # forward or transposed depends on matrix

            next_indices = set(next_vector.to_coo()[0])
            next_indices.difference_update(visited)

            if not next_indices:
                break

            visited.update(next_indices)
            current_vector = gb.Vector.from_coo(
                list(next_indices),
                [1] * len(next_indices),
                size=adjacency_matrix.nrows,
            )

            if distance is not None:
                distance -= 1

        return self.lookup_tables.index_to_term(list(visited))

    def _traverse_graph_with_distance(
        self,
        term_id: str,
        adjacency_matrix: gb.Matrix,
        include_self: bool = False,
    ) -> list:
        """Generalized function to traverse a graph and return nodes with distance from start.

        Parameters
        ----------
        term_id : str
            The starting term ID.
        adjacency_matrix : gb.Matrix
            Adjacency matrix to traverse (forward for descendants, transposed for ancestors).
        include_self : bool
            Whether to include the starting node with distance 0.

        Returns:
        -------
        List[Tuple[int, int]]
            List of tuples (node_index, distance_from_start)
        """
        if term_id not in self.lookup_tables.get_lut_term_to_index():
            raise KeyError(f'Unknown term ID: {term_id}')

        start_index = self.lookup_tables.term_to_index(term_id)
        current_vector = self.one_hot_vector(index=start_index)

        distances = {}  # {node_index: distance}
        distance_counter = 0

        if include_self:
            distances[start_index] = 0

        while current_vector.nvals != 0:
            next_vector = gb.Vector(dtype=int, size=adjacency_matrix.nrows)
            next_vector << gb.semiring.plus_times(
                adjacency_matrix @ current_vector
            )

            next_indices = set(next_vector.to_coo()[0])
            # remove already visited nodes
            next_indices.difference_update(distances.keys())

            if not next_indices:
                break

            distance_counter += 1
            for idx in next_indices:
                distances[idx] = distance_counter

            current_vector = gb.Vector.from_coo(
                list(next_indices),
                [1] * len(next_indices),
                size=adjacency_matrix.nrows,
            )

        # return as list of tuples
        return [
            (self.lookup_tables.index_to_term(int(index)), distance)
            for index, distance in distances.items()
        ]

    # -- get_parents(term_id, include_self=False)
    def get_parents(self, term_id: str, include_self: bool = False) -> list:
        # Validate and resolve the index
        if term_id not in self.lookup_tables.get_lut_term_to_index():
            raise KeyError(f'Unknown term ID: {term_id}')

        index = self.lookup_tables.term_to_index(term_id)

        # Initialize a one-hot vector for the term node
        vector_node = self.one_hot_vector(index=index)

        # Propagate to parents using matrix-vector multiplication
        parent_vec = (self.matrices_container['is_a'].T @ vector_node).new()

        # Extract parent indices efficiently
        parent_indices = set(parent_vec.to_coo()[0])
        if include_self:
            parent_indices.add(index)

        # Convert indices to term IDs
        return self.lookup_tables.index_to_term(list(parent_indices))

    # -- get_root()
    def get_root(self) -> list:
        matrix = self.matrices_container['is_a'].T

        # 1. Compute the number of incoming edges per node (column-wise sum)
        col_sums_expr = matrix.reduce_columnwise(gb.binary.plus)

        # 2. Materialize the VectorExpression
        col_sums_vec = col_sums_expr.new()

        # 3. Extract non-zero indices and their counts
        indices, values = col_sums_vec.to_coo()

        # 4. Create dense array of incoming edge counts
        col_sums_np = np.zeros(matrix.ncols, dtype=np.int64)
        col_sums_np[indices] = values

        # 5. Roots = nodes with zero incoming edges
        roots = np.where(col_sums_np == 0)[0]

        return self.lookup_tables.index_to_term(roots)

    def get_term(self, term_id: str) -> object:
        """Retrieve the ontology term object for a given term ID."""
        pass

    # -- get_children(term_id, include_self=False)
    def get_children(self, term_id: str, include_self: bool = False) -> list:
        # validate and resolve the index
        if term_id not in self.lookup_tables.get_lut_term_to_index():
            raise KeyError(f'Unknown term ID: {term_id}')

        index = self.lookup_tables.term_to_index(term_id)

        # Initialize a one-hot vector for the term node
        vector_node = self.one_hot_vector(index=index)

        # Propagate to children using matrix-vector multiplication
        children_vec = (self.matrices_container['is_a'] @ vector_node).new()

        # Optionally include the node itself
        if include_self:
            children_vec[index] = True

        # translate indexes to terms
        terms = list(children_vec)

        return self.lookup_tables.index_to_term(terms)

    def get_ancestors(
        self, term_id: str, distance: int = None, include_self: bool = False
    ) -> list:
        adjacency_matrix = self.matrices_container[
            'is_a'
        ].T  # transpose for ancestors
        return self._traverse_graph(
            term_id, adjacency_matrix, distance, include_self
        )

    def get_ancestors_with_distance(
        self, term_id: str, include_self: bool = False
    ) -> list:
        adjacency_matrix = self.matrices_container[
            'is_a'
        ].T  # transpose for ancestors
        return self._traverse_graph_with_distance(
            term_id, adjacency_matrix, include_self
        )

    def get_descendants(
        self, term_id: str, distance: int = None, include_self: bool = False
    ) -> list:
        adjacency_matrix = self.matrices_container[
            'is_a'
        ]  # normal direction for descendants
        return self._traverse_graph(
            term_id, adjacency_matrix, distance, include_self
        )

    def get_descendants_with_distance(
        self, term_id: str, include_self: bool = False
    ) -> list:
        adjacency_matrix = self.matrices_container[
            'is_a'
        ]  # normal direction for descendants
        return self._traverse_graph_with_distance(
            term_id, adjacency_matrix, include_self
        )

    def get_siblings(
        self, term_id: str, include_self: bool = False
    ) -> list[str]:
        """Retrieve all siblings of a given term (i.e., nodes that share at least one parent).

        Parameters
        ----------
        term_id : str
            The term ID whose siblings are to be found.
        include_self : bool, optional (default=False)
            Whether to include the term itself in the returned set.

        Returns:
        -------
        List[str]
            List of sibling term IDs.
        """
        # Validate term existence
        if term_id not in self.lookup_tables.get_lut_term_to_index():
            raise KeyError(f'Unknown term ID: {term_id}')

        # Step 1: Get parents of the given term
        parents = self.get_parents(term_id, include_self=False)
        if not parents:
            # No parents means this term is a root -> no siblings
            return []

        # Step 2: For each parent, get its children
        siblings_set = set()
        for parent_id in parents:
            children = self.get_children(parent_id, include_self=False)
            siblings_set.update(children)

        # Step 3: Optionally remove the term itself
        if not include_self and term_id in siblings_set:
            siblings_set.remove(term_id)

        # Return as sorted list for deterministic output
        return sorted(siblings_set)
