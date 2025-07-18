"""Tests for the ontology_query module."""

from pathlib import Path
from collections.abc import Callable

from pronto import Ontology
import pytest

from ontograph.ontology_query import OntologyQueries

__all__ = [
    'mock_ontology',
    'query_helper',
    'test_ancestors_basic',
    'test_ancestors_root',
    'test_ancestors_with_self',
    'test_children_basic',
    'test_children_leaf',
    'test_children_root',
    'test_descendants_basic',
    'test_descendants_leaf',
    'test_descendants_with_self',
    'test_get_term_existing',
    'test_get_term_nonexistent',
    'test_init_with_invalid_ontology',
    'test_nonexistent_term_operations',
    'test_parents_basic',
    'test_parents_multiple',
    'test_parents_root',
]


# --------------------------
# ----     FIXTURES     ----
# --------------------------
@pytest.fixture
def mock_ontology(tmp_path: Path) -> Ontology:
    """Create a small test ontology file and load it with Pronto.

    The test ontology has the following structure:
        root (GO:0000000)
        ├── term1 (GO:0000001)
        │   ├── term3 (GO:0000003)
        │   └── term4 (GO:0000004)
        └── term2 (GO:0000002)
            └── term5 (GO:0000005)
    """
    # Create a small test ontology
    test_ontology = """
    format-version: 1.2
    ontology: go

    [Term]
    id: GO:0000000
    name: root

    [Term]
    id: GO:0000001
    name: term1
    is_a: GO:0000000 ! root

    [Term]
    id: GO:0000002
    name: term2
    is_a: GO:0000000 ! root

    [Term]
    id: GO:0000003
    name: term3
    is_a: GO:0000001 ! term1

    [Term]
    id: GO:0000004
    name: term4
    is_a: GO:0000001 ! term1

    [Term]
    id: GO:0000005
    name: term5
    is_a: GO:0000002 ! term2
    """
    # Write the test ontology to a temporary file
    ontology_file = tmp_path / 'test_ontology.obo'
    ontology_file.write_text(test_ontology)

    # Load the ontology using Pronto
    return Ontology(str(ontology_file))


@pytest.fixture
def query_helper(mock_ontology: Ontology) -> OntologyQueries:
    """Create an OntologyQueries instance with the mock ontology."""
    return OntologyQueries(mock_ontology)


# --------------------------
# ----    UNIT TESTS    ----
# --------------------------
def test_init_with_invalid_ontology() -> None:
    """Test that initializing with invalid ontology raises TypeError."""
    with pytest.raises(
        TypeError, match='ontology must be a pronto.Ontology object'
    ):
        OntologyQueries('not an ontology')


def test_get_term_existing(query_helper: OntologyQueries) -> None:
    """Test retrieving an existing term."""
    term = query_helper.get_term('GO:0000001')
    assert term.id == 'GO:0000001'
    assert term.name == 'term1'


def test_get_term_nonexistent(query_helper: OntologyQueries) -> None:
    """Test retrieving a non-existent term raises KeyError."""
    with pytest.raises(KeyError):
        query_helper.get_term('GO:9999999')


def test_ancestors_basic(query_helper: OntologyQueries) -> None:
    """Test getting ancestors for a term with known ancestors."""
    # term3 should have term1 and root as ancestors
    ancestors = query_helper.ancestors('GO:0000003')
    assert ancestors == {'GO:0000001', 'GO:0000000'}


def test_ancestors_with_self(query_helper: OntologyQueries) -> None:
    """Test getting ancestors with include_self=True."""
    ancestors = query_helper.ancestors('GO:0000003', include_self=True)
    assert ancestors == {'GO:0000003', 'GO:0000001', 'GO:0000000'}


def test_ancestors_root(query_helper: OntologyQueries) -> None:
    """Test getting ancestors for the root term."""
    ancestors = query_helper.ancestors('GO:0000000', include_self=False)
    assert ancestors == set()


def test_descendants_basic(query_helper: OntologyQueries) -> None:
    """Test getting descendants for a term with known descendants."""
    # term1 should have term3 and term4 as descendants
    descendants = query_helper.descendants('GO:0000001')
    assert descendants == {'GO:0000003', 'GO:0000004'}


def test_descendants_with_self(query_helper: OntologyQueries) -> None:
    """Test getting descendants with include_self=True."""
    descendants = query_helper.descendants('GO:0000001', include_self=True)
    assert descendants == {'GO:0000001', 'GO:0000003', 'GO:0000004'}


def test_descendants_leaf(query_helper: OntologyQueries) -> None:
    """Test getting descendants for a leaf term."""
    descendants = query_helper.descendants('GO:0000003')
    assert descendants == set()


def test_parents_basic(query_helper: OntologyQueries) -> None:
    """Test getting direct parents for a term."""
    # term3 should have term1 as its only parent
    parent = query_helper.parent('GO:0000003')
    assert parent == {'GO:0000001'}


def test_parents_root(query_helper: OntologyQueries) -> None:
    """Test getting parents for the root term."""
    parents = query_helper.parent('GO:0000000')
    assert parents == set()


def test_parents_multiple(query_helper: OntologyQueries) -> None:
    """Test getting parents when term has multiple parents."""
    # TODO
    assert True


def test_children_basic(query_helper: OntologyQueries) -> None:
    """Test getting direct children for a term."""
    # term1 should have term3 and term4 as children
    children = query_helper.children('GO:0000001')
    assert children == {'GO:0000003', 'GO:0000004'}


def test_children_leaf(query_helper: OntologyQueries) -> None:
    """Test getting children for a leaf term."""
    children = query_helper.children('GO:0000003')
    assert children == set()


def test_children_root(query_helper: OntologyQueries) -> None:
    """Test getting children for the root term."""
    children = query_helper.children('GO:0000000')
    assert children == {'GO:0000001', 'GO:0000002'}


def test_nonexistent_term_operations(query_helper: OntologyQueries) -> None:
    """Test that operations with non-existent terms raise KeyError."""
    operations: list[Callable[[], set[str]]] = [
        lambda: query_helper.ancestors('GO:9999999'),
        lambda: query_helper.descendants('GO:9999999'),
        lambda: query_helper.parent('GO:9999999'),
        lambda: query_helper.children('GO:9999999'),
    ]

    for operation in operations:
        with pytest.raises(KeyError):
            operation()
