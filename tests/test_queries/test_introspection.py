from pathlib import Path

import pytest

from ontograph.loader import ProntoLoaderAdapter
from ontograph.queries.navigator import OntologyNavigator
from ontograph.queries.relations import OntologyRelations
from ontograph.queries.introspection import OntologyIntrospection


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
def dummy_relations(dummy_navigator):
    return OntologyRelations(dummy_navigator)


@pytest.fixture
def dummy_introspection(dummy_navigator, dummy_relations):
    return OntologyIntrospection(dummy_navigator, dummy_relations)


# -----------------------------------
# ----         Unit Tests        ----
# -----------------------------------


# ---- Function get_distance_from_root()
def test_get_distance_from_root_root_term(dummy_introspection, dummy_navigator):
    # The root term should have distance 0 from itself
    root_term = dummy_navigator.get_root()[0]
    distance = dummy_introspection.get_distance_from_root(root_term.id)
    assert distance == 0


def test_get_distance_from_root_direct_child(
    dummy_introspection, dummy_navigator
):
    # Pick a direct child of root and check its distance is 1
    assert dummy_introspection.get_distance_from_root('C') == 1
    assert dummy_introspection.get_distance_from_root('D') == 2
    assert dummy_introspection.get_distance_from_root('F') == 3
    assert dummy_introspection.get_distance_from_root('Z') == 0


def test_get_distance_from_root_nonexistent_term(dummy_introspection):
    # Should return None or raise for a term that does not exist
    with pytest.raises(KeyError):
        dummy_introspection.get_distance_from_root('FAKE:0000000')


# ---- Function get_path_between()
def test_get_path_between_ancestor_descendant(dummy_introspection):
    # C is a direct child of Z (root), path should be Z -> C
    path = dummy_introspection.get_path_between('Z', 'C')
    ids = [node['id'] for node in path]

    assert ids == ['Z', 'C']


def test_get_path_between_descendant_ancestor(dummy_introspection):
    # C is a direct child of Z (root), path should be Z -> C
    path = dummy_introspection.get_path_between('C', 'Z')
    ids = [node['id'] for node in path]

    assert ids == ['Z', 'C']


def test_get_path_between_indirect_path(dummy_introspection):
    # F is a descendant of A, path should be F -> D -> A
    path = dummy_introspection.get_path_between('A', 'F')
    ids = [node['id'] for node in path]
    distances = [node['distance'] for node in path]
    assert ids == ['A', 'D', 'F']
    assert distances == [0, 1, 2]


def test_get_path_between_no_relationship(dummy_introspection):
    # If there is no ancestor-descendant relationship, should return empty list
    path = dummy_introspection.get_path_between('C', 'FAKE:0000000')
    assert path == []


def test_get_path_between_self(dummy_introspection):
    # Path from a node to itself should be just that node
    path = dummy_introspection.get_path_between('C', 'C')
    ids = [node['id'] for node in path]
    assert ids == ['C']


# ---- Function get_trajectories_from_root()
def test_get_trajectories_from_root_single_path(dummy_introspection):
    # For a leaf node, should return a single trajectory from root to the term
    trajectories = dummy_introspection.get_trajectories_from_root('F')

    # Each trajectory is a list of dicts with id, name, distance
    assert isinstance(trajectories, list)
    assert len(trajectories) == 1
    ids = [node['id'] for node in trajectories[0]]

    # Should start at F and end at root Z
    assert ids[0] == 'Z'
    assert ids[-1] == 'F'
    assert ids == ['Z', 'A', 'D', 'F']


def test_get_trajectories_from_root_multiple_paths(dummy_introspection):
    # If a term has multiple paths to root (multiple inheritance), all should be returned
    # For dummy ontology, let's assume D has two parents: A and B, both under Z
    trajectories = dummy_introspection.get_trajectories_from_root('Y')

    assert isinstance(trajectories, list)
    # Should have at least one trajectory
    assert len(trajectories) >= 1

    # All trajectories should end at root Z
    # for traj in trajectories:
    #    assert traj[-1]["id"] == "Z"


def test_get_trajectories_from_root_root_term(dummy_introspection):
    # For the root term, trajectory should be just itself
    trajectories = dummy_introspection.get_trajectories_from_root('Z')
    assert len(trajectories) == 1
    assert trajectories[0][0]['id'] == 'Z'
    assert trajectories[0][0]['distance'] == 0


def test_print_term_trajectories_tree_empty(capsys):
    OntologyIntrospection.print_term_trajectories_tree([])
    out, _ = capsys.readouterr()
    assert 'No trajectories to display.' in out


def test_print_term_trajectories_tree_simple(capsys):
    trajectories = [
        [
            {'id': 'Z', 'name': 'root', 'distance': 0},
            {'id': 'A', 'name': 'A', 'distance': 1},
            {'id': 'D', 'name': 'D', 'distance': 2},
        ]
    ]
    OntologyIntrospection.print_term_trajectories_tree(trajectories)
    out, _ = capsys.readouterr()
    assert 'Z: root' in out
    assert 'A: A' in out
    assert 'D: D' in out


def test_build_tree_from_trajectories_structure():
    trajectories = [
        [
            {'id': 'Z', 'name': 'root', 'distance': 0},
            {'id': 'A', 'name': 'A', 'distance': 1},
        ],
        [
            {'id': 'Z', 'name': 'root', 'distance': 0},
            {'id': 'B', 'name': 'B', 'distance': 1},
        ],
    ]
    root = OntologyIntrospection._build_tree_from_trajectories(trajectories)
    assert root.id == 'Z'
    assert 'A' in [c.name for c in root.children.values()]
    assert 'B' in [c.name for c in root.children.values()]


def test_print_ascii_tree(capsys):
    class Node:
        def __init__(self, node_id, name, distance):
            self.id = node_id
            self.name = name
            self.distance = distance
            self.children = {}

    root = Node('Z', 'root', 0)
    root.children[('A', 'A', 1)] = Node('A', 'A', 1)
    root.children[('B', 'B', 1)] = Node('B', 'B', 1)
    OntologyIntrospection._print_ascii_tree(root)
    out, _ = capsys.readouterr()
    assert 'Z: root' in out
    assert 'A: A' in out
    assert 'B: B' in out


def test_get_distance_from_root_term_exception(
    dummy_introspection, monkeypatch
):
    def raise_exc(term_id):
        raise RuntimeError('Term not found')

    monkeypatch.setattr(
        dummy_introspection._OntologyIntrospection__navigator,
        'get_term',
        raise_exc,
    )
    with pytest.raises(RuntimeError):
        dummy_introspection.get_distance_from_root('X')


def test_get_distance_from_root_root_exception(
    dummy_introspection, monkeypatch
):
    monkeypatch.setattr(
        dummy_introspection._OntologyIntrospection__navigator,
        'get_root',
        lambda: [],
    )
    assert dummy_introspection.get_distance_from_root('A') is None


def test_get_path_between_navigator_exception(dummy_introspection):
    assert dummy_introspection.get_path_between('A', 'C') == []


def test_get_trajectories_from_root_superclasses_attribute_error(
    dummy_introspection, monkeypatch
):
    # Should return [] when superclasses raises AttributeError
    class DummyTerm:
        id = 'A'
        name = 'A'

        def superclasses(self, distance=1):
            raise AttributeError('fail')

    monkeypatch.setattr(
        dummy_introspection._OntologyIntrospection__navigator,
        'get_term',
        lambda tid: DummyTerm(),
    )
    assert dummy_introspection.get_trajectories_from_root('A') == []


def test_get_trajectories_from_root_superclasses_type_error(
    dummy_introspection, monkeypatch
):
    # Should return [] when superclasses raises TypeError
    class DummyTerm:
        id = 'A'
        name = 'A'

        def superclasses(self, distance=1):
            raise TypeError('fail')

    monkeypatch.setattr(
        dummy_introspection._OntologyIntrospection__navigator,
        'get_term',
        lambda tid: DummyTerm(),
    )
    assert dummy_introspection.get_trajectories_from_root('A') == []
