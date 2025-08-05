from pathlib import Path

import pytest

from ontograph.loader import ProntoLoaderAdapter
from ontograph.queries.navigator import OntologyNavigator
from ontograph.queries.relations import OntologyRelations


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
def dummy_navigator(dummy_ontology):
    return OntologyNavigator(dummy_ontology)


@pytest.fixture
def relations(dummy_navigator):
    return OntologyRelations(dummy_navigator)


@pytest.fixture
def dummy_relations(dummy_navigator):
    return OntologyRelations(dummy_navigator)


# -----------------------------------
# ----         Unit Tests        ----
# -----------------------------------


# ---- Function: is_ancestor()
def test_is_ancestor_true(relations):
    # These should be true in your main dummy ontology
    assert relations.is_ancestor('A', 'D') is True
    assert relations.is_ancestor('A', 'K2') is True
    assert relations.is_ancestor('B', 'K') is True
    assert relations.is_ancestor('S', 'U') is True


def test_is_ancestor_false(relations, dummy_relations):
    assert relations.is_ancestor('D', 'A') is False
    assert relations.is_ancestor('B', 'Z') is False
    assert relations.is_ancestor('H', 'B') is False
    assert relations.is_ancestor('K1', 'K2') is False

    assert dummy_relations.is_ancestor('', '') is False


def test_is_ancestor_self(relations):
    # Should be False because include_self=False
    assert relations.is_ancestor('A', 'A') is False
    assert relations.is_ancestor('B', 'B') is False


def test_is_ancestor_invalid_id(dummy_relations):
    assert dummy_relations.is_ancestor('invalid', 'child') is False


def test_is_ancestor_exception(relations, monkeypatch):
    # Patch get_ancestors to raise Exception
    monkeypatch.setattr(
        relations._OntologyRelations__navigator,
        'get_ancestors',
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError('fail')),
    )
    with pytest.raises(RuntimeError):
        relations.is_ancestor('A', 'D')


# ---- Function: is_descendant()
def test_is_descendant_true(relations):
    assert relations.is_descendant('D', 'A') is True
    assert relations.is_descendant('K2', 'A') is True
    assert relations.is_descendant('K', 'B') is True
    assert relations.is_descendant('U', 'S') is True


def test_is_descendant_false(relations):
    assert relations.is_descendant('A', 'D') is False
    assert relations.is_descendant('Z', 'B') is False
    assert relations.is_descendant('B', 'H') is False
    assert relations.is_descendant('K2', 'K1') is False


def test_is_descendant_self(relations):
    # Should be False because include_self=False
    assert relations.is_descendant('A', 'A') is False
    assert relations.is_descendant('B', 'B') is False


def test_is_descendant_exception(relations, monkeypatch):
    monkeypatch.setattr(
        relations._OntologyRelations__navigator,
        'get_descendants',
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError('fail')),
    )
    with pytest.raises(RuntimeError):
        relations.is_descendant('D', 'A')


# ---- Function: is_sibling()
def test_is_sibling_true(relations):
    # These should be siblings (share at least one parent, not the same node)
    assert relations.is_sibling('K1', 'K2') is True
    assert relations.is_sibling('F', 'E') is True
    assert relations.is_sibling('W', 'V') is True


def test_is_sibling_false(relations):
    # These should not be siblings (no shared parent or same node)
    assert relations.is_sibling('A', 'A') is False  # same node
    assert relations.is_sibling('A', 'K1') is False  # no shared parent
    assert relations.is_sibling('B', 'Z') is False


def test_is_sibling_no_shared_parent(relations):
    # Nodes with no shared parent
    assert relations.is_sibling('K', 'L') is False


def test_is_sibling_handles_runtime_error_gracefully(relations, monkeypatch):
    instances = []

    class DummyTerm:
        def __init__(self):
            instances.append(self)

        def superclasses(self, _distance=1, _with_self=False):
            raise RuntimeError('fail')

    monkeypatch.setattr(
        relations._OntologyRelations__navigator,
        'get_term',
        lambda _x: DummyTerm(),
    )

    result = relations.is_sibling('B', 'A')

    # Verify result fallback
    assert result is False or result is None

    # Verify get_term was called twice
    assert len(instances) == 2

    # Verify both are instances of DummyTerm
    assert all(isinstance(obj, DummyTerm) for obj in instances)


# ---- Function: get_common_ancestors()
def test_get_common_ancestors_basic(relations):
    # Nodes K1 and K2 should share common ancestors A and K
    result = relations.get_common_ancestors(['K1', 'K2'])
    assert 'G' in result


def test_get_common_ancestors_self(relations):
    # Single node should return itself as ancestor
    result = relations.get_common_ancestors(['A'])
    assert result == {'A', 'Z'}


def test_get_common_ancestors_empty(relations):
    # Empty input should return empty set
    result = relations.get_common_ancestors([])
    assert result == set()


def test_get_common_ancestors_no_common(relations):
    # Nodes with no common ancestor
    result = relations.get_common_ancestors(['A', 'Z'])
    assert result == {'Z'}


def test_get_common_ancestors_multiple_nodes(relations):
    # Multiple nodes with a shared ancestor
    result = relations.get_common_ancestors(['N', 'O', 'G'])
    assert 'A' in result
    assert 'D' in result
    assert 'Z' in result


def test_get_common_ancestors_outer_exception(relations, monkeypatch):
    monkeypatch.setattr(
        relations._OntologyRelations__navigator,
        'get_ancestors',
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError('fail')),
    )
    with pytest.raises(RuntimeError):
        relations.get_common_ancestors(['A', 'B'])


def test_get_common_ancestors_inner_exception(relations, monkeypatch):
    def fail_on_B(node_id, include_self=True):
        if node_id == 'B':
            raise RuntimeError('fail')
        return {'A'}

    monkeypatch.setattr(
        relations._OntologyRelations__navigator, 'get_ancestors', fail_on_B
    )
    with pytest.raises(RuntimeError):
        relations.get_common_ancestors(['A', 'B'])


# ---- Function: get_lowest_common_ancestors()
def test_get_lowest_common_ancestors_basic(relations):
    # K1 and K2 should have G as their lowest common ancestor
    result = relations.get_lowest_common_ancestors(['K1', 'K2'])
    assert 'G' in result


def test_get_lowest_common_ancestors_self(relations):
    # Single node should return itself as lowest common ancestor
    result = relations.get_lowest_common_ancestors(['A'])
    assert result == {'A'}


def test_get_lowest_common_ancestors_empty(relations):
    # Empty input should return empty set
    with pytest.raises(ValueError):
        relations.get_lowest_common_ancestors([])


def test_get_lowest_common_ancestors_no_common(relations, monkeypatch):
    # Patch get_common_ancestors to return empty set
    monkeypatch.setattr(relations, 'get_common_ancestors', lambda _: set())
    with pytest.raises(ValueError):
        relations.get_lowest_common_ancestors(['A', 'B'])


def test_get_lowest_common_ancestors_multiple_nodes(relations):
    # Multiple nodes with a shared lowest ancestor
    result = relations.get_lowest_common_ancestors(['N', 'O', 'G'])
    assert 'D' in result or 'A' in result or 'Z' in result


# ---- Function: get_distance_to_ancestor()
def test_get_distance_to_ancestor_basic(relations):
    # Basic distance checks
    assert relations._get_distance_to_ancestor('D', 'A') == 1
    assert relations._get_distance_to_ancestor('K2', 'A') == 3
    assert relations._get_distance_to_ancestor('K', 'B') == 2
    assert relations._get_distance_to_ancestor('U', 'S') == 2


def test_get_distance_to_ancestor_no_ancestor(relations):
    # No ancestor relationship
    assert relations._get_distance_to_ancestor('A', 'C') == float('inf')


def test_get_distance_to_ancestor_self(relations):
    # Distance to self should be 0
    assert relations._get_distance_to_ancestor('A', 'A') == 0


def test_get_distance_to_ancestor_exception(relations, monkeypatch):
    monkeypatch.setattr(
        relations._OntologyRelations__navigator,
        'get_term',
        lambda x: (_ for _ in ()).throw(RuntimeError('fail')),
    )
    with pytest.raises(RuntimeError):
        relations._get_distance_to_ancestor('A', 'Z')


def test_get_distance_to_ancestor_traversal_exception(relations, monkeypatch):
    class DummyTerm:
        id = 'A'

        def superclasses(self, distance=1, with_self=False):
            raise RuntimeError('fail')

    monkeypatch.setattr(
        relations._OntologyRelations__navigator,
        'get_term',
        lambda x: DummyTerm(),
    )
    with pytest.raises(RuntimeError):
        relations._get_distance_to_ancestor('A', 'Z')
