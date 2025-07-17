"""Interface for querying and navigating ontology terms and their relationships."""

import sys

from pronto.term import Term
from pronto.ontology import Ontology

__all__ = [
    'OntologyQueries',
]


class OntologyQueries:
    """Query helper for navigating a Pronto ontology.

    This class provides methods to retrieve and navigate relationships between terms
    in an ontology, including ancestry (superclasses), descendants (subclasses),
    and direct parent-child relationships.

    Attributes:
        ont: A pronto.Ontology instance containing the ontology data.
    """

    def __init__(self, ontology: Ontology) -> None:
        """Initialize with a Pronto Ontology object.

        Args:
            ontology: A pronto.Ontology instance containing the ontology data.

        Raises:
            TypeError: If ontology is not a pronto.Ontology object.
        """
        if not isinstance(ontology, Ontology):
            raise TypeError('ontology must be a pronto.Ontology object')
        self.ont = ontology

    def get_term(self, term_id: str) -> Term:
        """Retrieve a pronto.Term object by its identifier.

        Args:
            term_id: The identifier of the term (e.g., 'GO:0008150').

        Returns:
            Term: A pronto.Term object representing the requested term.

        Raises:
            KeyError: If the term is not found in the ontology.
        """
        return self.ont[term_id]

    def ancestors(self, term_id: str, include_self: bool = False) -> set[str]:
        """Get all ancestor term IDs of a given term (transitive parents).

        Args:
            term_id: Identifier of the term to find ancestors for.
            include_self: If True, include the term itself in the result.

        Returns:
            set[str]: A set of ancestor term IDs, including all terms in the path
                from the given term to the root of the ontology.

        Raises:
            KeyError: If the term_id is not found in the ontology.
        """
        term = self.get_term(term_id)
        ancestor_ids = {ancestor.id for ancestor in term.superclasses()}
        if include_self:
            ancestor_ids.add(term.id)
        else:
            ancestor_ids.remove(term_id)
        return ancestor_ids

    def descendants(self, term_id: str, include_self: bool = False) -> set[str]:
        """Get all descendant term IDs of a given term (transitive children).

        Args:
            term_id: Identifier of the term to find descendants for.
            include_self: If True, include the term itself in the result.

        Returns:
            set[str]: A set of descendant term IDs, including all terms that have
                the given term as an ancestor.

        Raises:
            KeyError: If the term_id is not found in the ontology.
        """
        term = self.get_term(term_id)
        descendant_ids = {descendant.id for descendant in term.subclasses()}
        if include_self:
            descendant_ids.add(term.id)
        else:
            descendant_ids.remove(term.id)
        return descendant_ids

    def parent(self, term_id: str) -> set[str]:
        """Get the direct parent term IDs of a given term.

        Args:
            term_id: Identifier of the term to find parents for.

        Returns:
            set[str]: A set of term IDs representing the immediate parents
                (direct superclasses) of the given term.

        Raises:
            KeyError: If the term_id is not found in the ontology.
        """
        term = self.get_term(term_id)
        parent_id = {
            parent_term.id for parent_term in term.superclasses(distance=1)
        }
        parent_id.remove(term_id)
        return parent_id

    def children(self, term_id: str) -> set[str]:
        """Get the direct child term IDs of a given term.

        Args:
            term_id: Identifier of the term to find children for.

        Returns:
            set[str]: A set of term IDs representing the immediate children
                (direct subclasses) of the given term.

        Raises:
            KeyError: If the term_id is not found in the ontology.
        """
        term = self.get_term(term_id)
        # Direct children are subclasses at distance=1
        children = {child.id for child in term.subclasses(distance=1)}
        children.remove(term_id)
        return children


if __name__ == '__main__':
    try:
        from pronto import Ontology

        # Load the Gene Ontology from a local file or URL
        print('Loading Gene Ontology...')
        go = Ontology('http://purl.obolibrary.org/obo/go.obo')
        queries = OntologyQueries(go)

        # Example term: "biological_process" (GO:0008150)
        example_term = 'GO:0008150'
        print(f'\nDemonstrating queries for term: {example_term}')

        # Get term information
        term = queries.get_term(example_term)
        print(f'\nTerm: {term.name} ({term.id})')
        print(f'Definition: {term.definition}')

        # Get immediate parents and children
        parents = queries.parents(example_term)
        children = queries.children(example_term)
        print(f'\nDirect parents: {len(parents)}')
        for parent_id in parents:
            parent = queries.get_term(parent_id)
            print(f'- {parent.name} ({parent.id})')

        print(f'\nDirect children (first 5): {len(children)}')
        for child_id in list(children)[:5]:
            child = queries.get_term(child_id)
            print(f'- {child.name} ({child.id})')

        # Get all ancestors and descendants
        ancestors = queries.ancestors(example_term)
        descendants = queries.descendants(example_term)
        print(f'\nTotal ancestors: {len(ancestors)}')
        print(f'Total descendants: {len(descendants)}')
    except KeyError as e:
        print(f'Error: Term not found - {str(e)}', file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f'Error: Invalid value - {str(e)}', file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f'Error: System error - {str(e)}', file=sys.stderr)
        sys.exit(1)
