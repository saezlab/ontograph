import logging
from collections import deque
from collections.abc import Iterator

from ontograph.models import Ontology

__all__ = [
    'OntologyNavigator',
]

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class OntologyNavigator:
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
