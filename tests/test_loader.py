from pathlib import Path

import pytest

from ontograph.loader import (
    OntologyLoaderPort,
    ProntoLoaderAdapter,
)
from ontograph.models import Ontology


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
def pronto_loader(resources_dir):
    return ProntoLoaderAdapter(cache_dir=resources_dir)


# Tests for OntologyLoaderPort (ABC)
def test_ontology_loader_port_is_abstract():
    with pytest.raises(TypeError):
        OntologyLoaderPort()


# -----------------------------------
# ----         Unit Tests        ----
# -----------------------------------


# ---- Function: load_from_file()
def test_load_from_file_success(pronto_loader, dummy_ontology_path):
    ontology = pronto_loader.load_from_file(dummy_ontology_path)
    assert isinstance(ontology, Ontology)
    assert hasattr(ontology, '_ontology')
    assert hasattr(ontology, '_ontology_id')
    assert ontology._ontology_id is not None
    assert len(ontology._ontology.terms()) > 0


def test_load_from_file_not_found(pronto_loader):
    with pytest.raises(FileNotFoundError):
        pronto_loader.load_from_file('nonexistent.obo')


def test_load_from_file_value_error(pronto_loader, tmp_path, monkeypatch):
    # Create a dummy file
    file_path = tmp_path / 'bad.obo'
    file_path.write_text('bad content')

    # Patch pronto.Ontology to raise ValueError
    monkeypatch.setattr(
        'pronto.Ontology', lambda fp: (_ for _ in ()).throw(ValueError('fail'))
    )
    with pytest.raises(ValueError):
        pronto_loader.load_from_file(file_path)


# ---- Function: load_from_catalog()
def test_load_from_catalog_unsupported_format(pronto_loader):
    with pytest.raises(ValueError):
        pronto_loader.load_from_catalog('ado', format='unsupported')


def test_load_from_catalog_file_not_found(pronto_loader, monkeypatch):
    # Patch Path.exists to always return False
    monkeypatch.setattr(Path, 'exists', lambda self: False)
    # Patch _download_ontology to raise FileNotFoundError
    monkeypatch.setattr(
        pronto_loader,
        '_download_ontology',
        lambda name_id, format: (_ for _ in ()).throw(
            FileNotFoundError('fail')
        ),
    )
    with pytest.raises(FileNotFoundError):
        pronto_loader.load_from_catalog('ado', format='obo')


def test_load_from_catalog_metadata_missing(
    pronto_loader, monkeypatch, tmp_path
):
    # Patch file existence and _download_ontology to return a dummy file
    file_path = tmp_path / 'ado.obo'
    file_path.write_text('dummy')
    monkeypatch.setattr(
        pronto_loader, '_download_ontology', lambda name_id, format: file_path
    )
    monkeypatch.setattr(
        pronto_loader,
        '_load_ontology',
        lambda fp: (
            type(
                'DummyOntology',
                (),
                {'metadata': type('Meta', (), {'annotations': {}})},
            )(),
            None,
        ),
    )
    # Patch catalog.get_ontology_metadata to return None
    monkeypatch.setattr(
        pronto_loader.catalog, 'get_ontology_metadata', lambda ontology_id: None
    )
    # Should not fail even if metadata is missing
    result = pronto_loader.load_from_catalog('ado', format='obo')
    assert isinstance(result, Ontology)


# Function: load_from_url()
def test_load_from_url_not_implemented(pronto_loader, monkeypatch):
    class DummyDownloader:
        def fetch_from_url(self, url_ontology, filename):
            raise FileNotFoundError('fail')

    with pytest.raises(FileNotFoundError):
        pronto_loader.load_from_url(
            'http://invalid-url', 'invalid.obo', downloader=DummyDownloader()
        )


def test_load_from_url_downloader_error(pronto_loader, monkeypatch):
    class DummyDownloader:
        def fetch_from_url(self, url_ontology, filename):
            raise FileNotFoundError('fail')

    with pytest.raises(FileNotFoundError):
        pronto_loader.load_from_url(
            'http://example.com/ado.obo',
            'ado.obo',
            downloader=DummyDownloader(),
        )


def test_load_from_url_load_ontology_error(
    pronto_loader, monkeypatch, tmp_path
):
    class DummyDownloader:
        def fetch_from_url(self, url_ontology, filename):
            # Use pytest's tmp_path fixture for a safe temp file
            temp_file = tmp_path / 'ado.obo'
            temp_file.write_text('dummy content')
            return temp_file

    monkeypatch.setattr(
        pronto_loader,
        '_load_ontology',
        lambda fp: (_ for _ in ()).throw(ValueError('fail')),
    )
    with pytest.raises(ValueError):
        pronto_loader.load_from_url(
            'http://example.com/ado.obo',
            'ado.obo',
            downloader=DummyDownloader(),
        )


def test_download_ontology_not_implemented(pronto_loader, monkeypatch):
    # Patch downloader.fetch_from_catalog to raise Exception
    class DummyDownloader:
        def fetch_from_catalog(self, resources, catalog):
            raise Exception('fail')

    monkeypatch.setattr(
        'ontograph.loader.PoochDownloaderAdapter',
        lambda cache_dir: DummyDownloader(),
    )
    with pytest.raises(NotImplementedError):
        pronto_loader._download_ontology('ado', 'obo')


def test_cache_dir_property_value_error():
    loader = ProntoLoaderAdapter(cache_dir=None)
    loader._cache_dir = None
    with pytest.raises(ValueError):
        _ = loader.cache_dir


def test_extract_ontology_id_attribute_error(pronto_loader):
    class DummyOntology:
        metadata = None

    # Should return None if metadata is missing
    assert pronto_loader._extract_ontology_id(DummyOntology()) is None


def test_extract_ontology_id_key_error(pronto_loader, monkeypatch):
    class DummyOntology:
        metadata = type('Meta', (), {})()

        # No 'ontology' attribute

    assert pronto_loader._extract_ontology_id(DummyOntology()) is None


def test_extract_ontology_id_type_error(pronto_loader):
    class DummyOntology:
        metadata = 'not a meta object'

    assert pronto_loader._extract_ontology_id(DummyOntology()) is None


def test_load_ontology_type_error(pronto_loader, tmp_path, monkeypatch):
    # Create a dummy file
    file_path = tmp_path / 'bad.obo'
    file_path.write_text('bad content')

    # Patch pronto.Ontology to raise TypeError
    monkeypatch.setattr(
        'pronto.Ontology', lambda fp: (_ for _ in ()).throw(TypeError('fail'))
    )
    with pytest.raises(ValueError):
        pronto_loader._load_ontology(file_path)
