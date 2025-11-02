import logging
from abc import ABC, abstractmethod
from collections import deque

from ontograph.queries.navigator import OntologyNavigator as _OntologyNavigator

__all__ = [
    'OntologyRelations',
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# --------------------------------------------------------
# ----     OntologyRelations Port (abstract class)    ----
# --------------------------------------------------------
class OntologyRelations(ABC):
    """Abstract class for querying relationships between ontology terms."""

    def __init__(self, navigator) -> None:
        self._navigator = navigator

    @abstractmethod
    def is_ancestor(self, ancestor_node: str, descendant_node: str) -> bool:
        """Determines if `ancestor_node` is an ancestor of `descendant_node`."""
        pass

    @abstractmethod
    def is_descendant(self, descendant_node: str, ancestor_node: str) -> bool:
        """Determines if `descendant_node` is a descendant of `ancestor_node`."""
        pass

    @abstractmethod
    def is_sibling(self, node_a: str, node_b: str) -> bool:
        """Determine if two nodes are siblings (share at least one parent)."""
        pass

    @abstractmethod
    def get_common_ancestors(self, node_ids: list[str]) -> set:
        """Finds the common ancestors of a list of nodes."""
        pass

    @abstractmethod
    def get_lowest_common_ancestors(self, node_ids: list[str]) -> set:
        """Finds the lowest common ancestors among a set of nodes."""
        pass

# ---------------------------------------------------------
# ----     RelationsPronto adapter (abstract class)    ----
# ---------------------------------------------------------
class RelationsPronto(OntologyRelations):
    """Provides methods for querying relationships between ontology terms.

    Includes ancestor, descendant, sibling checks, and common ancestor computations.
    """

    def __init__(self, navigator: _OntologyNavigator) -> None:
        """Initialize OntologyRelations.

        Args:
            navigator (_OntologyNavigator): The ontology navigator instance.
        """
        self.__navigator = navigator

    def is_ancestor(self, ancestor_node: str, descendant_node: str) -> bool:
        """Determines if `ancestor_node` is an ancestor of `descendant_node`.

        Args:
            ancestor_node (str): The ID of the potential ancestor term.
            descendant_node (str): The ID of the potential descendant term.

        Returns:
            bool: True if `ancestor_node` is an ancestor of `descendant_node`, False otherwise.

        Raises:
            Exception: If an unexpected error occurs during ancestor lookup.
        """
        try:
            ancestors = self.__navigator.get_ancestors(
                descendant_node, include_self=False
            )
            return ancestor_node in ancestors
        except Exception as e:
            logger.error(f'Error checking ancestor relationship: {e}')
            raise

    def is_descendant(self, descendant_node: str, ancestor_node: str) -> bool:
        """Determines if `descendant_node` is a descendant of `ancestor_node`.

        Args:
            descendant_node (str): The ID of the potential descendant term.
            ancestor_node (str): The ID of the potential ancestor term.

        Returns:
            bool: True if `descendant_node` is a descendant of `ancestor_node`, False otherwise.

        Raises:
            Exception: If an unexpected error occurs during descendant lookup.
        """
        try:
            descendants = self.__navigator.get_descendants(
                ancestor_node, include_self=False
            )
            return descendant_node in descendants
        except Exception as e:
            logger.error(f'Error checking descendant relationship: {e}')
            raise

    def is_sibling(self, node_a: str, node_b: str) -> bool:
        """Determine if two nodes are siblings (share at least one parent).

        Siblings are defined as nodes that are not the same and share at least one parent (i.e., their sets of parents intersect).

        Args:
            node_a (str): The ID of the first node.
            node_b (str): The ID of the second node.

        Returns:
            bool: True if the nodes are siblings (not the same node and share at least one parent), False otherwise.

        Raises:
            KeyError: If either node_a or node_b is not found in the ontology.
            Exception: If an error occurs during parent lookup.
        """
        try:
            parentsA = set(self.__navigator.get_parents(term_id=node_a))
            parentsB = set(self.__navigator.get_parents(term_id=node_b))

            # Siblings must not be the same node and must share at least one parent
            return node_a != node_b and bool(parentsA & parentsB)
        except Exception as e:
            logger.error(f'Error checking sibling relationship: {e}')
            raise

    def _get_distance_to_ancestor(
        self, node: str, ancestor: str
    ) -> int | float:
        """Calculate the shortest distance from a node to a specified ancestor.

        Args:
            node (str): The ID of the starting node.
            ancestor (str): The ID of the ancestor node to find.

        Returns:
            int: The shortest distance (number of edges) from `node` to `ancestor`.
            float: Returns float("inf") if no path exists.

        Raises:
            Exception: If an error occurs during term lookup or traversal.
        """
        try:
            term = self.__navigator.get_term(node)
        except Exception as e:
            logger.error(f"Error retrieving term for node '{node}': {e}")
            raise

        visited = set()
        queue = deque([(term, 0)])
        while queue:
            try:
                current, dist = queue.popleft()
                if current.id == ancestor:
                    return dist
                if current.id in visited:
                    continue
                visited.add(current.id)
                for parent in current.superclasses(distance=1, with_self=False):
                    if parent.id not in visited:
                        queue.append((parent, dist + 1))
            except Exception as e:
                logger.error(f'Error during ancestor traversal: {e}')
                raise
        return float('inf')

    def get_common_ancestors(self, node_ids: list[str]) -> set:
        """Finds the common ancestors of a list of nodes.

        Args:
            node_ids (list[str]): List of node IDs to find common ancestors for.

        Returns:
            set: Set of common ancestor IDs. Returns an empty set if there are no common ancestors or if input is empty.

        Raises:
            Exception: If an error occurs during ancestor lookup for any node.
        """
        if not node_ids:
            return set()

        ancestor_sets = []
        try:
            for node_id in node_ids:
                try:
                    ancestors = set(
                        self.__navigator.get_ancestors(
                            node_id, include_self=True
                        )
                    )
                    ancestor_sets.append(ancestors)
                except Exception as e:
                    logger.error(
                        f"Error retrieving ancestors for node '{node_id}': {e}"
                    )
                    raise
            common_ancestors = set.intersection(*ancestor_sets)
            logger.debug(f'Common ancestors: {common_ancestors}')
        except Exception as e:
            logger.error(f'Error during common ancestor computation: {e}')
            raise

        return common_ancestors

    def get_lowest_common_ancestors(self, node_ids: list[str]) -> set:
        """Finds the lowest common ancestors among a set of nodes.

        This method computes the common ancestors for the given node IDs and determines
        which of these ancestors are the lowest (i.e., have the minimal maximal distance
        from any of the nodes in the input set).

        Args:
            node_ids (Iterable[Any]): An iterable of node identifiers for which to find the lowest common ancestors.

        Returns:
            Set[Any]: A set of node identifiers representing the lowest common ancestors.

        Raises:
            ValueError: If there are no common ancestors (i.e., the input sequence is empty).
        """

        common_ancestors = self.get_common_ancestors(node_ids)

        # For each common ancestor, calculate its max distance from all nodes
        distances = {}
        for ancestor in common_ancestors:
            max_dist = max(
                self._get_distance_to_ancestor(node_id, ancestor)
                for node_id in node_ids
            )
            distances[ancestor] = max_dist
        logger.debug(f'Distances: {distances}')

        try:
            min_distance = min(distances.values())
        except ValueError as e:
            logger.exception(f'Empty sequence: {e}')
            raise

        lowest_common = {
            anc for anc, dist in distances.items() if dist == min_distance
        }
        return lowest_common

# ------------------------------------------------------------
# ----     RelationsGraphblas adapter (abstract class)    ----
# ------------------------------------------------------------
class RelationsGraphblas(OntologyRelations):
    def __init__(self, navigator: _OntologyNavigator, lookup_tables) -> None:
        """Initialize OntologyRelations.

        Args:
            navigator (_OntologyNavigator): The ontology navigator instance.
        """
        self.__navigator = navigator
        self.lookup_tables = lookup_tables

    def is_ancestor(self, ancestor_node, descendant_node):
        """
        Check if `ancestor_node` is an ancestor of `descendant_node`.

        Parameters
        ----------
        ancestor_node : str
            Candidate ancestor term ID.
        descendant_node : str
            Candidate descendant term ID.

        Returns
        -------
        bool
            True if `ancestor_node` is an ancestor of `descendant_node`, else False.
        """
        if descendant_node not in self.lookup_tables.get_lut_term_to_index():
            raise KeyError(f"Unknown term ID: {descendant_node}")
        if ancestor_node not in self.lookup_tables.get_lut_term_to_index():
            raise KeyError(f"Unknown term ID: {ancestor_node}")
        
        # Retrieve ancestors of the descendant
        ancestors = set(self.__navigator.get_ancestors(descendant_node, include_self=False))
        return ancestor_node in ancestors

    
    def is_descendant(self, descendant_node, ancestor_node):
        """
        Check if `descendant_node` is a descendant of `ancestor_node`.

        Parameters
        ----------
        descendant_node : str
            Candidate descendant term ID.
        ancestor_node : str
            Candidate ancestor term ID.

        Returns
        -------
        bool
            True if `descendant_node` is a descendant of `ancestor_node`, else False.
        """
        if ancestor_node not in self.lookup_tables.get_lut_term_to_index():
            raise KeyError(f"Unknown term ID: {ancestor_node}")
        if descendant_node not in self.lookup_tables.get_lut_term_to_index():
            raise KeyError(f"Unknown term ID: {descendant_node}")
        
        # Retrieve descendants of the ancestor
        descendants = set(self.get_descendants(ancestor_node, include_self=False))
        return descendant_node in descendants

    
    def is_sibling(self, node_a: str, node_b: str) -> bool:
        """
        Check if two nodes are siblings (i.e., share at least one common parent).

        Parameters
        ----------
        node_a : str
            First node (term ID).
        node_b : str
            Second node (term ID).

        Returns
        -------
        bool
            True if both nodes share at least one parent; False otherwise.
        """
        # Validate existence
        lut = self.lookup_tables.get_lut_term_to_index()
        if node_a not in lut:
            raise KeyError(f"Unknown term ID: {node_a}")
        if node_b not in lut:
            raise KeyError(f"Unknown term ID: {node_b}")

        # Step 1: Get parents for both nodes
        parents_a = set(self.get_parents(node_a, include_self=False))
        parents_b = set(self.get_parents(node_b, include_self=False))

        # Step 2: Intersection of parents indicates sibling relationship
        shared_parents = parents_a.intersection(parents_b)

        # Step 3: Return True if they share any parent
        return len(shared_parents) > 0

    
    def get_common_ancestors(self, node_ids):
        """
        Return the common ancestors of a list of terms.

        Parameters
        ----------
        node_ids : List[str]
            List of starting term IDs.
        include_self : bool
            Whether to include the starting nodes themselves in the ancestor sets.

        Returns
        -------
        List[str]
            List of term IDs that are common ancestors to all input terms.
        """
        if not node_ids:
            return []

        # get ancestors for the first node
        common_ancestors = set(self.get_ancestors(node_ids[0], include_self=False))

        # intersect with ancestors of the rest
        for term_id in node_ids[1:]:
            ancestors = set(self.get_ancestors(term_id, include_self=False))
            common_ancestors.intersection_update(ancestors)

            # early exit if no common ancestor remains
            if not common_ancestors:
                return []

        return set(common_ancestors)

    
    def get_lowest_common_ancestors(self, node_ids):
        """
        Return the lowest common ancestor(s) of a list of terms. 
        Lowest = closest to the given terms.

        Parameters
        ----------
        node_ids : List[str]
            List of starting term IDs.
        include_self : bool
            Whether to include the starting nodes in ancestor sets.

        Returns
        -------
        List[str]
            List of term IDs that are the lowest common ancestors.
        """
        if not node_ids:
            return []

        # Compute ancestors with distances for the first node
        first_ancestors = dict(self.get_ancestors_with_distance(node_ids[0], include_self=False))
        common_ancestors = set(first_ancestors.keys())

        # Initialize distances dict for LCA calculation
        # key: ancestor index, value: max distance from any node
        lca_distances = {idx: dist for idx, dist in first_ancestors.items()}

        # Process remaining nodes
        for term_id in node_ids[1:]:
            ancestors_with_distance = dict(self.get_ancestors_with_distance(term_id, include_self=False))
            ancestors_set = set(ancestors_with_distance.keys())
            common_ancestors.intersection_update(ancestors_set)

            # Update max distance for each common ancestor
            lca_distances = {idx: max(lca_distances[idx], ancestors_with_distance[idx])
                            for idx in common_ancestors}

            # Early exit if no common ancestor remains
            if not common_ancestors:
                return []

        if not lca_distances:
            return []

        # Find the minimum of the maximum distances
        min_distance = min(lca_distances.values())

        # Return ancestor IDs that have this minimum distance
        lowest_common_indices = [idx for idx, dist in lca_distances.items() if dist == min_distance]
        return lowest_common_indices