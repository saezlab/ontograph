from abc import ABC, abstractmethod
import logging
from collections import deque

from ontograph.models import LookUpTables
from ontograph.queries.navigator import NavigatorOntology
from ontograph.queries.relations import RelationsPronto, RelationsOntology

__all__ = [
    'IntrospectionOntology',
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# ------------------------------------------------------------
# ----     OntologyIntrospection Port (abstract class)    ----
# ------------------------------------------------------------
class IntrospectionOntology(ABC):
    """Abstract class for ontology introspection utilities."""

    def __init__(
        self, navigator: NavigatorOntology, relations: RelationsOntology
    ) -> None:
        self._navigator = navigator
        self._relations = relations

    @abstractmethod
    def get_distance_from_root(self, term_id: str) -> int | None:
        """Calculate the distance from a term to the ontology root."""
        pass

    @abstractmethod
    def get_path_between(self, node_a: str, node_b: str) -> list[dict]:
        """Find the trajectory (path) between two ontology terms."""
        pass

    @abstractmethod
    def get_trajectories_from_root(self, term_id: str) -> list[dict]:
        """Get all ancestor trajectories from the root to the given term."""
        pass

    @staticmethod
    @abstractmethod
    def print_term_trajectories_tree(trajectories: list[dict]) -> None:
        """Print all ancestor trajectories as a single ASCII tree from root to the original term."""
        pass

    # @staticmethod
    # @abstractmethod
    # def _build_tree_from_trajectories(trajectories: list[dict]) -> object:
    #     """Build a tree structure from the list of branches (trajectories)."""
    #     pass

    # @staticmethod
    # @abstractmethod
    # def _print_ascii_tree(root: object) -> None:
    #     """Print the tree structure in ASCII format starting from the root node."""
    #     pass


# -------------------------------------------------------------
# ----     IntrospectionPronto adapter (concrete class)    ----
# -------------------------------------------------------------
class IntrospectionPronto(IntrospectionOntology):
    """Provides introspection utilities for ontology graphs.

    Includes methods for calculating distances, paths, and ancestor trajectories.
    """

    def __init__(
        self, navigator: NavigatorOntology, relations: RelationsPronto
    ) -> None:
        """Initialize the introspection utility.

        Args:
            navigator (OntologyNavigator): The ontology navigator.
            relations (OntologyRelations): The ontology relations.
        """
        self.__navigator = navigator
        self.__relations = relations

    def get_distance_from_root(self, term_id: str) -> int | None:
        """Calculate the distance from a term to the ontology root.

        Args:
            term_id (str): The identifier of the term.

        Returns:
            int | None: The distance from the term to the root, or None if not found or an error occurs.

        Raises:
            Exception: If an unexpected error occurs during distance calculation.
        """
        try:
            self.__navigator.get_term(term_id)
        except (TypeError, AttributeError, ValueError) as e:
            logger.error(f"Error retrieving term for node '{term_id}': {e}")
            raise

        try:
            root = self.__navigator.get_root()[0].id
            logger.debug(f'Root: {root}')
        except (IndexError, AttributeError) as e:
            logger.error(f'Failed to get root: {e}')
            return None

        try:
            distance = self.__relations._get_distance_to_ancestor(term_id, root)
        except (TypeError, AttributeError, ValueError) as e:
            logger.error(
                f"Error calculating distance from '{term_id}' to root '{root}': {e}"
            )
            return None

        return distance

    def get_path_between(self, node_a: str, node_b: str) -> list[dict]:
        """Finds the trajectory (path) between two ontology terms if there is an ancestor-descendant relationship.

        Args:
            node_a (str): The ID of the first term.
            node_b (str): The ID of the second term.

        Returns:
            list[dict]: The path as a list of dictionaries with 'id' and 'distance' keys, or an empty list if no path exists.

        Raises:
            Exception: If an unexpected error occurs during path calculation.
        """
        if self.__relations.is_ancestor(
            ancestor_node=node_a, descendant_node=node_b
        ):
            start, end, step = node_a, node_b, 1
        elif self.__relations.is_ancestor(
            ancestor_node=node_b, descendant_node=node_a
        ):
            start, end, step = node_b, node_a, 1
        elif node_a == node_b:
            return [{'id': node_a, 'distance': 0}]
        else:
            return []

        try:
            term = self.__navigator.get_term(start)
        except (TypeError, AttributeError, ValueError) as e:
            logger.error(f"Error retrieving term for node '{start}': {e}")
            return []

        visited = set()
        queue = deque([(term, 0, [])])

        while queue:
            current_term, dist, current_path = queue.popleft()
            if current_term.id in visited:
                continue
            visited.add(current_term.id)
            new_path = current_path + [
                {'id': current_term.id, 'distance': dist}
            ]
            if current_term.id == end:
                return new_path

            try:
                for child in current_term.subclasses(distance=1):
                    if child.id not in visited:
                        queue.append((child, dist + step, new_path))
            except (TypeError, AttributeError, ValueError) as e:
                logger.error(
                    f"Error retrieving subclasses for term '{current_term.id}': {e}"
                )
                continue

        return []

    def get_trajectories_from_root(self, term_id: str) -> list[dict]:
        """Get all ancestor trajectories from the root to the given term.

        Args:
            term_id (str): The identifier of the term.

        Returns:
            list[dict]: List of trajectories, each trajectory is a list of dicts.
        """
        term = self.__navigator.get_term(term_id)
        trajectories = []

        def dfs(
            current_term: object,
            current_distance: int,
            path: list,
            visited: set,
        ) -> None:
            # Prevent cycles
            if current_term.id in visited:
                return
            # Add current term to path
            path = path + [
                {
                    'id': current_term.id,
                    'name': current_term.name,
                    'distance': current_distance,
                }
            ]
            try:
                parents = [
                    p
                    for p in current_term.superclasses(distance=1)
                    if p.id != current_term.id
                ]
            except (AttributeError, TypeError) as e:
                logger.error(
                    f"Error retrieving superclasses for term '{current_term.id}': {e}"
                )
                return
            if not parents:
                # Reached root, save this path
                trajectories.append(path[::-1])
                return
            for parent in parents:
                dfs(
                    parent,
                    current_distance - 1,
                    path,
                    visited | {current_term.id},
                )

        dfs(term, 0, [], set())
        return trajectories

    @staticmethod
    def print_term_trajectories_tree(trajectories: list[dict]) -> None:
        """Print all ancestor trajectories as a single ASCII tree from root to the original term.

        For a single trajectory, print each node as '{id}: {name}'.
        For multiple, print as ASCII tree.
        """
        if not trajectories:
            print('No trajectories to display.')
            return
        # If only one trajectory, print each node simply
        if len(trajectories) == 1:
            for node in trajectories[0]:
                print(f'{node["id"]}: {node["name"]}')
            return
        # Otherwise, use tree printing
        root = IntrospectionOntology._build_tree_from_trajectories(trajectories)
        IntrospectionOntology._print_ascii_tree(root)

    @staticmethod
    def _build_tree_from_trajectories(trajectories: list[dict]) -> object:
        """Build a tree structure from the list of branches (trajectories).

        Returns the root node.

        Args:
            trajectories (list[dict]): List of trajectory branches.

        Returns:
            object: The root node of the tree.
        """

        class Node:
            def __init__(self, node_id: str, name: str, distance: int) -> None:
                self.id = node_id
                self.name = name
                self.distance = distance
                self.children = {}

        def insert_branch(root: Node, branch: list) -> None:
            node = root
            for item in branch:
                key = (item['id'], item['name'], item['distance'])
                if key not in node.children:
                    node.children[key] = Node(*key)
                node = node.children[key]

        # All branches are sorted from term to root, so reverse to root-to-term
        branch_lists = [list(branch) for branch in trajectories]
        root_info = branch_lists[0][0]
        root = Node(root_info['id'], root_info['name'], root_info['distance'])
        for branch in branch_lists:
            insert_branch(root, branch[1:])  # skip root itself, already created
        return root

    @staticmethod
    def _print_ascii_tree(root: object) -> None:
        """Print the tree structure in ASCII format starting from the root node."""

        def print_ascii_tree(
            node: object, prefix: str = '', is_last: bool = True
        ) -> None:
            connector = '└── ' if is_last else '├── '
            print(
                f'{prefix}{connector}{node.id}: {node.name} (distance={node.distance})'
            )
            child_items = list(node.children.values())
            for idx, child in enumerate(child_items):
                is_last_child = idx == len(child_items) - 1
                next_prefix = prefix + ('    ' if is_last else '│   ')
                print_ascii_tree(child, next_prefix, is_last_child)

        # Print root without prefix
        print(f'{root.id}: {root.name} (distance={root.distance})')
        child_items = list(root.children.values())
        for idx, child in enumerate(child_items):
            is_last_child = idx == len(child_items) - 1
            print_ascii_tree(child, '', is_last_child)


class IntrospectionGraphblas(IntrospectionOntology):
    """Provides introspection utilities for ontology graphs using GraphBLAS.

    Includes methods for calculating distances, paths, and ancestor trajectories.
    """

    def __init__(
        self,
        navigator: NavigatorOntology,
        relations: RelationsOntology,
        lookup_tables: LookUpTables,
    ) -> None:
        """Initialize the introspection utility.

        Args:
            navigator (NavigatorPronto): The ontology navigator.
            relations (RelationsPronto): The ontology relations.
            lookup_tables (LookUpTables): Lookup tables for term/index/description mapping.
        """
        self.__navigator = navigator
        self.__relations = relations
        self.lookup_tables = lookup_tables
        self.matrices_container = navigator.matrices_container

    def get_distance_from_root(self, term_id: str) -> int:
        """Calculate the distance from the given term to the root node(s) of the ontology.

        Parameters
        ----------
        term_id : str
            The term ID for which to compute the distance from root.

        Returns:
        -------
        int
            Distance from the term to the root (number of edges).
            Returns 0 if the term is a root itself.
        """
        # Validate term
        if term_id not in self.lookup_tables.get_lut_term_to_index():
            raise KeyError(f'Unknown term ID: {term_id}')

        # Get all ancestors with distance
        ancestors_with_distance = self.__navigator.get_ancestors_with_distance(
            term_id, include_self=True
        )

        if not ancestors_with_distance:
            # No ancestors, this term is a root
            return 0

        # Distance from root = maximum distance in the ancestors path
        max_distance = max(distance for _, distance in ancestors_with_distance)

        return max_distance

    def get_path_between(self, node_a: str, node_b: str) -> list:
        """Find the shortest path between two nodes in the ontology.

        Parameters
        ----------
        node_a : str
            Starting term ID.
        node_b : str
            Ending term ID.

        Returns:
        -------
        List[str]
            List of term IDs representing the path from node_a to node_b (inclusive).
            Returns empty list if no path exists.
        """
        if node_a not in self.lookup_tables.get_lut_term_to_index():
            raise KeyError(f'Unknown term ID: {node_a}')
        if node_b not in self.lookup_tables.get_lut_term_to_index():
            raise KeyError(f'Unknown term ID: {node_b}')

        # Check if a path exists
        if not (
            self.__relations.is_ancestor(node_a, node_b)
            or self.__relations.is_descendant(node_a, node_b)
        ):
            return []

        # Determine direction
        if self.__relations.is_ancestor(node_a, node_b):
            start, end = node_a, node_b
            adjacency_matrix = self.matrices_container['is_a']
        else:
            start, end = node_b, node_a
            adjacency_matrix = self.matrices_container['is_a']

        start_idx = self.lookup_tables.term_to_index(start)
        end_idx = self.lookup_tables.term_to_index(end)

        # BFS to find shortest path

        queue = deque([[start_idx]])
        visited = {start_idx}

        while queue:
            path = queue.popleft()
            current = path[-1]

            if current == end_idx:
                return self.lookup_tables.index_to_term(path)

            # Get children (or parents depending on direction)
            neighbors_vec = adjacency_matrix @ self.__navigator.one_hot_vector(
                current
            )
            neighbors = neighbors_vec.to_coo()[0]

            for n in neighbors:
                if n not in visited:
                    visited.add(n)
                    queue.append(path + [n])

        return []

    def get_trajectories_from_root(self, term_id: str) -> list[list[dict]]:
        """Get all ancestor trajectories from the root(s) to the given term using GraphBLAS operations.

        Args:
            term_id (str): The identifier of the term.

        Returns:
            list[list[dict]]: List of trajectories; each trajectory is a list of dictionaries
                            with keys: 'id', 'name', and 'distance' (from the queried term).
        """
        # Validate input
        lut_term_to_index = self.lookup_tables.get_lut_term_to_index()
        if term_id not in lut_term_to_index:
            raise KeyError(f'Unknown term ID: {term_id}')

        A_T = self.matrices_container['is_a'].T
        term_idx = int(self.lookup_tables.term_to_index(term_id))

        # Root detection
        roots = set(self.__navigator.get_root())
        root_indices = {int(self.lookup_tables.term_to_index(r)) for r in roots}

        from collections import deque

        queue = deque([[term_idx]])
        trajectories = []

        while queue:
            path = queue.popleft()
            current_idx = int(path[0])

            # Parent discovery using GraphBLAS multiplication
            parent_vec = (
                A_T @ self.__navigator.one_hot_vector(current_idx)
            ).new()
            parent_indices = [int(i) for i in parent_vec.to_coo()[0]]

            # Termination condition: reached a root or no parents
            if not parent_indices or current_idx in root_indices:
                # Reverse path → root → term order
                reversed_path = list(reversed(path))
                traj = []
                for dist, idx in enumerate(
                    reversed_path[::-1]
                ):  # distance from term
                    idx = int(idx)
                    traj.append(
                        {
                            'id': self.lookup_tables.index_to_term(idx),
                            'name': self.lookup_tables.term_to_description(
                                self.lookup_tables.index_to_term(idx)
                            ),
                            'distance': dist,
                        }
                    )
                trajectories.append(
                    list(reversed(traj))
                )  # ensure root→term order
            else:
                for p in parent_indices:
                    if p not in path:
                        queue.append([p] + path)

        for traj in trajectories:
            traj.reverse()  # optional: reverse to have root-first order

        return trajectories  # optional: reverse to have root-first order

    @staticmethod
    def print_term_trajectories_tree(trajectories: list[dict]) -> None:
        """Print all ancestor trajectories as a single ASCII tree from root to the original term.

        Combining shared nodes.

        Args:
            trajectories: List of lists, each inner list is a trajectory (branch) as returned by ancestor_trajectories.
        """
        if not trajectories:
            print('No trajectories to display.')
            return
        root = IntrospectionGraphblas._build_tree_from_trajectories(
            trajectories
        )
        IntrospectionGraphblas._print_ascii_tree(root)

    @staticmethod
    def _build_tree_from_trajectories(trajectories: list[dict]) -> object:
        """Build a tree structure from the list of branches (trajectories).

        Returns the root node.

        Args:
            trajectories (list[dict]): List of trajectory branches.

        Returns:
            object: The root node of the tree.
        """

        class Node:
            def __init__(self, node_id: str, name: str, distance: int) -> None:
                self.id = node_id
                self.name = name
                self.distance = distance
                self.children = {}

        def insert_branch(root: Node, branch: list) -> None:
            node = root
            for item in branch:
                key = (item['id'], item['name'], item['distance'])
                if key not in node.children:
                    node.children[key] = Node(*key)
                node = node.children[key]

        # All branches are sorted from term to root, so reverse to root-to-term
        branch_lists = [list(branch) for branch in trajectories]
        root_info = branch_lists[0][0]
        root = Node(root_info['id'], root_info['name'], root_info['distance'])
        for branch in branch_lists:
            insert_branch(root, branch[1:])  # skip root itself, already created
        return root

    @staticmethod
    def _print_ascii_tree(root: object) -> None:
        """Print the tree structure in ASCII format starting from the root node."""

        def print_ascii_tree(
            node: object, prefix: str = '', is_last: bool = True
        ) -> None:
            connector = '└── ' if is_last else '├── '
            print(
                f'{prefix}{connector}{node.id}: {node.name} (distance={node.distance})'
            )
            child_items = list(node.children.values())
            for idx, child in enumerate(child_items):
                is_last_child = idx == len(child_items) - 1
                next_prefix = prefix + ('    ' if is_last else '│   ')
                print_ascii_tree(child, next_prefix, is_last_child)

        # Print root without prefix
        print(f'{root.id}: {root.name} (distance={root.distance})')
        child_items = list(root.children.values())
        for idx, child in enumerate(child_items):
            is_last_child = idx == len(child_items) - 1
            print_ascii_tree(child, '', is_last_child)
