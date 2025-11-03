from pathlib import Path

import pytest

from ontograph.loader import ProntoLoaderAdapter
from ontograph.queries.navigator import NavigatorPronto


# -----------------------------------
# ----      PyTest Fixtures      ----
# -----------------------------------
@pytest.fixture
def dummy_ontology(tmp_path):
    resources_dir = Path(__file__).parent.parent / 'resources'
    if not resources_dir.exists():
        raise FileNotFoundError(
            f'Resource directory does not exist: {resources_dir}'
        )

    obo_path = resources_dir / 'dummy_ontology.obo'
    if not obo_path.exists():
        raise FileNotFoundError(f'Ontology file not found: {obo_path}')

    try:
        loader = ProntoLoaderAdapter(cache_dir=resources_dir)
        ontology = loader.load_from_file(file_path_ontology=obo_path)
    except Exception as e:
        raise RuntimeError(f'Failed to load ontology from {obo_path}') from e

    return ontology


@pytest.fixture
def navigator(dummy_ontology):
    return NavigatorPronto(dummy_ontology)


# -----------------------------------
# ----         Unit Tests        ----
# -----------------------------------


# ---- Function: __get_term()
def test_get_term_valid_id(navigator):
    term = navigator.get_term(term_id='G')
    assert term.id == 'G'


def test_get_term_invalid_id_raises(navigator):
    with pytest.raises(KeyError):
        navigator.get_term('NON_EXISTENT_ID')


# ---- Function: get_parents()
def test_get_parents(navigator):
    assert set(navigator.get_parents(term_id='G', include_self=False)) == {
        'D',
        'K',
    }


def test_get_parents_include_self(navigator):
    assert set(navigator.get_parents('G', include_self=True)) == {'G', 'D', 'K'}


# ---- Function: get_children()
def test_get_children_basic(navigator):
    children = navigator.get_children('G')
    assert set(children) == {'K1', 'K2'}


def test_get_children_no_children(navigator):
    # This test assumes "Y" has no children in dummy_ontology.
    # If the ontology changes and "Y" gains children, update this test to use a term guaranteed to have no children.
    children = navigator.get_children('Y')
    assert children == []


def test_get_children_include_self(navigator):
    # Assuming "B" has child "D" in dummy_ontology
    children = navigator.get_children('D', include_self=True)
    # Should include "B" itself if present in children
    assert set(children) == {'D', 'E', 'F', 'G'}


def test_get_children_invalid_id(navigator):
    children = navigator.get_children('NON_EXISTENT_ID')
    assert children == []


# ---- Function: get_ancestors()
def test_get_ancestors_basic(navigator):
    # "G" should have ancestors "D" and "K"
    ancestors = navigator.get_ancestors('G')
    assert set(ancestors) == {'D', 'A', 'Z', 'K', 'H', 'B'}


def test_get_ancestors_include_self(navigator):
    # Including self should add "G" to the ancestors
    ancestors = navigator.get_ancestors('G', include_self=True)
    assert set(ancestors) == {'G', 'D', 'A', 'Z', 'K', 'H', 'B'}


def test_get_ancestors_distance_1(navigator):
    # Distance 1 should only return direct parents
    ancestors = navigator.get_ancestors('G', distance=1)
    assert set(ancestors) == {'D', 'K'}


def test_get_ancestors_distance_2(navigator):
    # Distance 2 should return parents and their parents
    ancestors = navigator.get_ancestors('G', distance=2)
    # The expected set depends on dummy_ontology structure
    # Example: {"D", "K", "B", "E"} if those are at distance 2
    assert set(ancestors) == {'D', 'A', 'K', 'H'}


def test_get_ancestors_no_ancestors(navigator):
    # "Z" assumed to be a root term with no ancestors
    ancestors = navigator.get_ancestors('Z')
    assert ancestors == []


def test_get_ancestors_invalid_id(navigator):
    ancestors = navigator.get_ancestors('NON_EXISTENT_ID')
    assert ancestors == []


# ---- Function: get_ancestors_with_distance()
def test_get_ancestors_with_distance_basic(navigator):
    # "F" should have ancestors with their distances
    # Example expected: ("F", 0), ("D", -1), ("A", -2), ("Z", -3)
    results = list(
        navigator.get_ancestors_with_distance('F', include_self=True)
    )
    ids_and_distances = {(term.id, dist) for term, dist in results}

    expected_ids_and_distances = {
        ('F', 0),
        ('D', -1),
        ('A', -2),
        ('Z', -3),
    }

    assert ids_and_distances == expected_ids_and_distances
    assert ('F', 0) in ids_and_distances


def test_get_ancestors_with_distance_no_self(navigator):
    results = list(
        navigator.get_ancestors_with_distance('G', include_self=False)
    )
    ids_and_distances = {(term.id, dist) for term, dist in results}
    # Should not include "G" itself
    returned_ids = {term_id for term_id, _ in ids_and_distances}
    assert 'G' not in returned_ids
    # All distances should be negative
    for _, dist in ids_and_distances:
        assert dist < 0


def test_get_ancestors_with_distance_root_term(navigator):
    # "Z" assumed to be a root term
    results = list(
        navigator.get_ancestors_with_distance('Z', include_self=True)
    )
    ids_and_distances = {(term.id, dist) for term, dist in results}
    # Only "Z" itself at distance 0
    assert ids_and_distances == {('Z', 0)}


def test_get_ancestors_with_distance_invalid_id(navigator):
    results = list(navigator.get_ancestors_with_distance('NON_EXISTENT_ID'))
    assert results == []


# ---- Function: get_descendants()
def test_get_descendants_basic(navigator):
    # "B" should have descendants "H" and "I"
    descendants = navigator.get_descendants('B')
    assert set(descendants) == {'H', 'K', 'Q', 'G', 'K1', 'K2', 'I', 'L'}


def test_get_descendants_include_self(navigator):
    # Including self should add "B" to the descendants
    descendants = navigator.get_descendants('B', include_self=True)
    assert set(descendants) == {'B', 'H', 'K', 'Q', 'G', 'K1', 'K2', 'I', 'L'}


def test_get_descendants_distance_1(navigator):
    # Distance 1 should only return direct children
    descendants = navigator.get_descendants('B', distance=1)
    assert set(descendants) == {'H', 'I'}


def test_get_descendants_distance_2(navigator):
    # Distance 2 should include children and their children
    descendants = navigator.get_descendants('M', distance=2)
    # The expected set depends on dummy_ontology structure
    # Example: {"S", "T"} if those exist

    assert set(descendants) == {'S', 'T'}  # At least direct children


def test_get_descendants_no_descendants(navigator):
    # "Y" assumed to have no descendants in dummy_ontology
    descendants = navigator.get_descendants('Y')
    assert descendants == set()


def test_get_descendants_invalid_id(navigator):
    descendants = navigator.get_descendants('NON_EXISTENT_ID')
    assert descendants == set()


# ---- Function: get_descendants_with_distance()
def test_get_descendants_with_distance_basic(navigator):
    # "B" should have descendants with their distances
    results = list(
        navigator.get_descendants_with_distance('B', include_self=True)
    )
    # Example expected: ("B", 0), ("H", 1), ("I", 1), ("K", 2), ("L", 2), ("Q", 3), ("G", 3), ("K1", 4), ("K2", 4)
    expected_ids_and_distances = {
        ('B', 0),
        ('H', 1),
        ('I', 1),
        ('K', 2),
        ('L', 2),
        ('Q', 3),
        ('G', 3),
        ('K1', 4),
        ('K2', 4),
    }
    ids_and_distances = {(term.id, dist) for term, dist in results}
    assert ids_and_distances == expected_ids_and_distances
    assert ('B', 0) in ids_and_distances
    # All distances should be >= 0
    for _, dist in ids_and_distances:
        assert dist >= 0


def test_get_descendants_with_distance_no_self(navigator):
    results = list(
        navigator.get_descendants_with_distance('B', include_self=False)
    )
    ids_and_distances = {(term.id, dist) for term, dist in results}
    returned_ids = {term_id for term_id, _ in ids_and_distances}
    assert 'B' not in returned_ids
    # All distances should be > 0
    for _, dist in ids_and_distances:
        assert dist > 0


def test_get_descendants_with_distance_leaf_term(navigator):
    # "Y" assumed to be a leaf term (no descendants)
    results = list(
        navigator.get_descendants_with_distance('N', include_self=True)
    )
    ids_and_distances = {(term.id, dist) for term, dist in results}
    assert ids_and_distances == {('N', 0)}


def test_get_descendants_with_distance_invalid_id(navigator):
    results = list(navigator.get_descendants_with_distance('NON_EXISTENT_ID'))
    assert results == []


# ---- Function: get_siblings()
def test_get_siblings_basic(navigator):
    # "G" should have siblings "E", "F", "Q" (assuming parents "D" and "K")
    siblings = navigator.get_siblings('G')
    assert set(siblings) == {'E', 'F', 'Q'}


def test_get_siblings_include_self(navigator):
    siblings = navigator.get_siblings('Y', include_self=True)
    assert set(siblings) == {'Y', 'O'}


def test_get_siblings_no_siblings(navigator):
    # "Z" assumed to be a root term with no siblings
    siblings = navigator.get_siblings('Z')
    assert siblings == set()


def test_get_siblings_leaf_term(navigator):
    # "N" assumed to be a leaf term with no siblings
    siblings = navigator.get_siblings('N')
    assert siblings == set()


def test_get_siblings_invalid_id(navigator):
    siblings = navigator.get_siblings('NON_EXISTENT_ID')
    assert siblings == set()


# ---- Function: get_root()
def test_get_root_basic(navigator):
    # Assuming "Z" is a root term in dummy_ontology
    roots = navigator.get_root()
    root_ids = {term.id for term in roots}
    assert 'Z' in root_ids
    # If there are multiple roots, check their IDs
    # Example: assert root_ids == {"Z", "ROOT2"}


def test_get_root_no_roots(monkeypatch, navigator):
    # Monkeypatch __ontology.terms to simulate no root terms
    class DummyTerm:
        def superclasses(self, distance=1, with_self=False):
            return [object()]  # Always has a superclass

    monkeypatch.setattr(
        navigator._NavigatorPronto__ontology, 'terms', lambda: [DummyTerm()]
    )
    roots = navigator.get_root()
    assert roots == []


def test_get_root_exception(monkeypatch, navigator):
    # Monkeypatch __ontology.terms to raise an exception
    monkeypatch.setattr(
        navigator._NavigatorPronto__ontology,
        'terms',
        lambda: (_ for _ in () if False),
    )
    # Should handle exception and return []
    roots = navigator.get_root()
    assert roots == []
