import logging
from collections import deque

from ontograph.queries.navigator import OntologyNavigator as _OntologyNavigator

__all__ = [
    'OntologyRelations',
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class OntologyRelations:
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

    def is_sibling(self, nodeA: str, nodeB: str) -> bool:
        """Determine if two nodes are siblings (share at least one parent).

        Args:
            nodeA (str): The ID of the first node.
            nodeB (str): The ID of the second node.

        Returns:
            bool: True if the nodes are siblings (not the same node and share at least one parent), False otherwise.

        Raises:
            Exception: If an error occurs during parent lookup.
        """
        try:
            parentsA = {
                parent.id
                for parent in self.__navigator.get_term(nodeA).superclasses(
                    distance=1, with_self=False
                )
            }
            parentsB = {
                parent.id
                for parent in self.__navigator.get_term(nodeB).superclasses(
                    distance=1, with_self=False
                )
            }
            # Siblings must not be the same node and must share at least one parent
            return nodeA != nodeB and bool(parentsA & parentsB)
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
