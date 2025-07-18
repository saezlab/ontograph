from pathlib import Path
import tempfile
from unittest.mock import patch

import pytest

from ontograph.client import OntoRegistryClient

__all__ = [
    'client',
    'mock_adapter',
    'temp_cache_dir',
    'test_get_available_formats',
    'test_get_download_url',
    'test_get_ontology_metadata',
    'test_list_available_ontologies',
    'test_load_registry',
    'test_print_registry_schema_tree',
    'test_registry_as_dict',
]


@pytest.fixture
def mock_adapter():
    """Fixture to mock OBORegistryAdapter."""
    with patch('ontograph.client.OBORegistryAdapter') as MockAdapter:
        adapter = MockAdapter.return_value
        adapter.registry = {'ontology1': {'id': 'ontology1'}}
        adapter.list_available_ontologies.return_value = [
            'ontology1',
            'ontology2',
        ]
        adapter.get_ontology_metadata.return_value = {
            'id': 'ontology1',
            'name': 'Ontology 1',
        }
        adapter.get_download_url.return_value = (
            'http://example.com/ontology1.obo'
        )
        adapter.get_available_formats.return_value = ['obo', 'json']
        yield adapter


@pytest.fixture
def temp_cache_dir():
    """Fixture to provide a temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def client(mock_adapter, temp_cache_dir):
    """Fixture to create an OntoRegistryClient instance."""
    return OntoRegistryClient(cache_dir=temp_cache_dir)


def test_load_registry(client, mock_adapter):
    """Test load_registry method."""
    client.load_registry(force_download=True)
    mock_adapter.load_registry.assert_called_once_with(force_download=True)


def test_registry_as_dict(client, mock_adapter):
    """Test registry_as_dict method."""
    result = client.registry_as_dict()
    assert result == {'ontology1': {'id': 'ontology1'}}


def test_list_available_ontologies(client, mock_adapter):
    """Test list_available_ontologies method."""
    result = client.list_available_ontologies()
    assert result == ['ontology1', 'ontology2']


def test_print_registry_schema_tree(client, mock_adapter):
    """Test print_registry_schema_tree method."""
    client.print_registry_schema_tree()
    mock_adapter.print_registry_schema_tree.assert_called_once()


def test_get_ontology_metadata(client, mock_adapter):
    """Test get_ontology_metadata method."""
    result = client.get_ontology_metadata('ontology1')
    assert result == {'id': 'ontology1', 'name': 'Ontology 1'}
    mock_adapter.get_ontology_metadata.assert_called_once_with(
        'ontology1', show_metadata=False
    )


def test_get_download_url(client, mock_adapter):
    """Test get_download_url method."""
    result = client.get_download_url('ontology1', format='obo')
    assert result == 'http://example.com/ontology1.obo'
    mock_adapter.get_download_url.assert_called_once_with('ontology1', 'obo')


def test_get_available_formats(client, mock_adapter):
    """Test get_available_formats method."""
    result = client.get_available_formats('ontology1')
    assert result == ['obo', 'json']
    mock_adapter.get_available_formats.assert_called_once_with('ontology1')
