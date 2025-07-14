# ontology_queries.py

from typing import Set
import pronto


class OntologyQueries:
    """
    Query helper for navigating a Pronto ontology.

    Provides methods to retrieve ancestors, descendants, parents, and children
    of terms in an ontology.
    """

    def __init__(self, ontology: pronto.Ontology):
        """
        Initialize with a Pronto Ontology object.

        :param ontology: A pronto.Ontology instance.
        """
        if not isinstance(ontology, pronto.Ontology):
            raise TypeError("ontology must be a pronto.Ontology object")
        self.ont = ontology

    def get_term(self, term_id: str) -> pronto.Term:
        """
        Retrieve a pronto.Term object by its identifier.

        :param term_id: The identifier of the term (e.g., 'GO:0008150').
        :return: pronto.Term object.
        :raises KeyError: if the term is not found in the ontology.
        """
        return self.ont[term_id]

    def ancestors(self, term_id: str, include_self: bool = False) -> Set[str]:
        """
        Get all ancestor term IDs of a given term (transitive parents).

        :param term_id: Identifier of the term.
        :param include_self: If True, include the term itself in the result.
        :return: A set of ancestor term IDs.
        """
        term = self.get_term(term_id)
        ancestor_ids = {ancestor.id for ancestor in term.superclasses()}
        if include_self:
            ancestor_ids.add(term.id)
        return ancestor_ids

    def descendants(self, term_id: str, include_self: bool = False) -> Set[str]:
        """
        Get all descendant term IDs of a given term (transitive children).

        :param term_id: Identifier of the term.
        :param include_self: If True, include the term itself in the result.
        :return: A set of descendant term IDs.
        """
        term = self.get_term(term_id)
        descendant_ids = {descendant.id for descendant in term.subclasses()}
        if include_self:
            descendant_ids.add(term.id)
        return descendant_ids

    def parents(self, term_id: str) -> Set[str]:
        """
        Get the direct parent term IDs of a given term.

        :param term_id: Identifier of the term.
        :return: A set of direct parent term IDs.
        """
        term = self.get_term(term_id)
        # Direct parents are superclasses at distance=1
        return {parent.id for parent in term.superclasses(distance=5)}

    def children(self, term_id: str) -> Set[str]:
        """
        Get the direct child term IDs of a given term.

        :param term_id: Identifier of the term.
        :return: A set of direct child term IDs.
        """
        term = self.get_term(term_id)
        # Direct children are subclasses at distance=1
        return {child.id for child in term.subclasses(distance=1)}
