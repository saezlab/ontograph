from pathlib import Path

import pytest

from ontograph.client import ClientCatalog, ClientOntology
from ontograph.models import Ontology

__all__ = [
    'client_catalog',
    'client_ontology',
    'dummy_ontology_path',
    'resources_dir',
    'test_catalog_as_dict_type',
    'test_client_ontology_introspection_methods',
    'test_client_ontology_load_from_file',
    'test_client_ontology_load_invalid_strategy',
    'test_client_ontology_load_multiple_strategies',
    'test_client_ontology_navigation_methods',
    'test_client_ontology_relations_methods',
    'test_get_download_url_and_formats',
    'test_get_ontology_metadata_returns_dict',
    'test_load_catalog_and_list_ontologies',
]

# -----------------------------------
# ----      PyTest Fixtures      ----
# -----------------------------------


@pytest.fixture
def resources_dir():
    return Path(__file__).parent / 'resources'


@pytest.fixture
def dummy_ontology_path(resources_dir):
    return resources_dir / 'dummy_ontology.obo'


@pytest.fixture
def client_catalog(resources_dir):
    # Use a test cache directory
    return ClientCatalog(cache_dir=resources_dir)


@pytest.fixture
def client_ontology(resources_dir):
    return ClientOntology(cache_dir=resources_dir)


# -----------------------------------
# ----         Unit Tests        ----
# -----------------------------------


def test_load_catalog_and_list_ontologies(client_catalog):
    # Should load catalog and list available ontologies (may be empty if no catalog present)
    client_catalog.load_catalog(force_download=False)
    ontologies = client_catalog.list_available_ontologies()
    print(ontologies)
    assert isinstance(ontologies, list)
    # No assertion on content, as catalog may be empty in test env


def test_catalog_as_dict_type(client_catalog):
    # Should return a dict representing the catalog
    catalog_dict = client_catalog.catalog_as_dict()
    assert isinstance(catalog_dict, dict)


def test_get_ontology_metadata_returns_dict(client_catalog):
    # Should return metadata dict for a valid ontology id, or raise for invalid
    client_catalog.load_catalog()
    ontologies = client_catalog.list_available_ontologies()

    if ontologies:
        ontology_id = ontologies[0]['id']
        meta = client_catalog.get_ontology_metadata(ontology_id=ontology_id)
        assert isinstance(meta, dict)
    else:
        # If no ontologies, expect KeyError
        with pytest.raises(KeyError):
            client_catalog.get_ontology_metadata('nonexistent_id')


def test_get_download_url_and_formats(client_catalog):
    client_catalog.load_catalog()
    ontologies = client_catalog.list_available_ontologies()

    if ontologies:
        # Determine ontology_id based on type
        first_ontology = ontologies[0]
        ontology_id = first_ontology['id']

        try:
            url = client_catalog.get_download_url(
                ontology_id=ontology_id,
            )
        except ValueError:
            url = client_catalog.get_download_url(
                ontology_id=ontology_id, format='owl'
            )

        assert isinstance(url, str)
        formats = client_catalog.get_available_formats(first_ontology)
        assert isinstance(formats, list)
    else:
        # Should raise for missing ontology
        with pytest.raises(KeyError):
            client_catalog.get_download_url('nonexistent_id')
        with pytest.raises(KeyError):
            client_catalog.get_available_formats('nonexistent_id')


# ---- Test ClientOntology


def test_client_ontology_load_from_file(client_ontology, dummy_ontology_path):
    # Should load ontology from file and initialize queries
    ontology = client_ontology.load(file_path_ontology=str(dummy_ontology_path))
    assert isinstance(ontology, Ontology)
    # Should be able to access root term
    root = client_ontology.get_root()
    assert isinstance(root, list)
    assert root[0].id == 'Z'


def test_client_ontology_load_invalid_strategy(client_ontology):
    # Should raise ValueError if no strategy is provided
    with pytest.raises(ValueError):
        client_ontology.load()


def test_client_ontology_load_multiple_strategies(
    client_ontology, dummy_ontology_path
):
    # Should raise ValueError if multiple strategies are provided
    with pytest.raises(ValueError):
        client_ontology.load(
            file_path_ontology=str(dummy_ontology_path),
            name_id='dummy',
            format='obo',
        )


def test_client_ontology_navigation_methods(
    client_ontology, dummy_ontology_path
):
    client_ontology.load(file_path_ontology=str(dummy_ontology_path))
    # Test navigation methods
    term = client_ontology.get_term('A')
    assert term.id == 'A'
    parents = client_ontology.get_parents('D')
    assert 'A' in parents
    children = client_ontology.get_children('A')
    assert 'D' in children
    ancestors = client_ontology.get_ancestors('D')
    assert 'A' in ancestors
    descendants = client_ontology.get_descendants('A')
    assert 'D' in descendants
    siblings = client_ontology.get_siblings('D')
    assert isinstance(siblings, set)


def test_client_ontology_relations_methods(
    client_ontology, dummy_ontology_path
):
    client_ontology.load(file_path_ontology=str(dummy_ontology_path))
    # Test relation methods
    assert client_ontology.is_ancestor('A', 'D') is True
    assert client_ontology.is_descendant('D', 'A') is True
    assert client_ontology.is_sibling('K1', 'K2') is True
    common_ancestors = client_ontology.get_common_ancestors(['K1', 'K2'])
    assert 'G' in common_ancestors


def test_client_ontology_introspection_methods(
    client_ontology, dummy_ontology_path
):
    client_ontology.load(file_path_ontology=str(dummy_ontology_path))
    # Test introspection methods
    distance = client_ontology.get_distance_from_root('D')
    assert isinstance(distance, int)
    path = client_ontology.get_path_between('A', 'D')
    assert isinstance(path, list)
    trajectories = client_ontology.get_trajectories_from_root('D')
    assert isinstance(trajectories, list)
