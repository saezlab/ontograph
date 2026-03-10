import pytest

from ontograph.models import (
    Ontology,
    CatalogOntologies,
)
import ontograph.models as models_module


@pytest.fixture
def dummy_catalog(tmp_path):
    # Create a dummy OBO Foundry registry YAML file
    catalog_data = {
        'ontologies': [
            {
                'id': 'chebi',
                'title': 'ChEBI',
                'products': [
                    {
                        'id': 'chebi.obo',
                        'ontology_purl': 'http://example.com/chebi.obo',
                    },
                    {
                        'id': 'chebi.owl',
                        'ontology_purl': 'http://example.com/chebi.owl',
                    },
                ],
            },
            {
                'id': 'ado',
                'title': 'ADO',
                'products': [
                    {
                        'id': 'ado.owl',
                        'ontology_purl': 'http://example.com/ado.owl',
                    },
                ],
            },
        ]
    }
    catalog_file = tmp_path / 'obofoundry_registry.yml'
    import yaml

    with open(catalog_file, 'w') as f:
        yaml.safe_dump(catalog_data, f)
    return catalog_file, catalog_data


@pytest.fixture
def catalogontologies(tmp_path, dummy_catalog, monkeypatch):
    catalog_file, _ = dummy_catalog
    # Monkeypatch config to use our dummy file
    from ontograph.config import settings

    monkeypatch.setattr(settings, 'NAME_OBO_FOUNDRY_CATALOG', catalog_file.name)
    obo_reg = CatalogOntologies(cache_dir=tmp_path)
    obo_reg.load_catalog()
    return obo_reg


def test_list_available_ontologies(catalogontologies):
    ontologies = catalogontologies.list_available_ontologies()
    assert isinstance(ontologies, list)
    assert any(o['id'] == 'chebi' for o in ontologies)
    assert any(o['id'] == 'ado' for o in ontologies)


def test_get_ontology_metadata_valid_and_invalid(catalogontologies):
    meta = catalogontologies.get_ontology_metadata('chebi')
    assert isinstance(meta, dict)
    assert meta['id'] == 'chebi'
    assert catalogontologies.get_ontology_metadata('nonexistent') is None


def test_get_download_url_success(catalogontologies):
    url = catalogontologies.get_download_url('chebi', 'obo')
    assert url == 'http://example.com/chebi.obo'
    url2 = catalogontologies.get_download_url('chebi', 'owl')
    assert url2 == 'http://example.com/chebi.owl'
    url3 = catalogontologies.get_download_url('ado', 'owl')
    assert url3 == 'http://example.com/ado.owl'


def test_get_download_url_failure(catalogontologies):
    with pytest.raises(ValueError):
        catalogontologies.get_download_url('chebi', 'missing')
    with pytest.raises(ValueError):
        catalogontologies.get_download_url('nonexistent', 'obo')


def test_get_available_formats(catalogontologies):
    formats = catalogontologies.get_available_formats('chebi')
    assert 'chebi.obo' in formats
    assert 'chebi.owl' in formats
    formats2 = catalogontologies.get_available_formats('ado')
    assert 'ado.owl' in formats2
    formats3 = catalogontologies.get_available_formats('nonexistent')
    assert formats3 == []


def test_print_available_ontologies(catalogontologies, capsys):
    catalogontologies.print_available_ontologies()
    out, _ = capsys.readouterr()
    assert 'name ID' in out
    assert 'chebi' in out
    assert 'ADO' in out


def test_print_catalog_schema_tree(catalogontologies, capsys):
    catalogontologies.print_catalog_schema_tree()
    out, _ = capsys.readouterr()
    assert 'OBO Foundry Registry Schema Structure' in out


def test_load_catalog_uses_default_downloader(tmp_path, monkeypatch):
    catalog_file = tmp_path / 'registry.yml'
    catalog_data = {'ontologies': []}

    def write_catalog():
        import yaml

        with open(catalog_file, 'w') as f:
            yaml.safe_dump(catalog_data, f)

    class DummyDownloader:
        def fetch_from_url(self, url_ontology, filename):
            write_catalog()
            return catalog_file

    calls = {'count': 0}

    def fake_get_default(cache_dir):
        calls['count'] += 1
        return DummyDownloader()

    monkeypatch.setattr(
        models_module, 'NAME_OBO_FOUNDRY_CATALOG', catalog_file.name
    )
    monkeypatch.setattr(
        models_module, 'get_default_downloader', fake_get_default
    )

    obo_reg = CatalogOntologies(cache_dir=tmp_path)
    obo_reg.load_catalog(force_download=True)
    assert calls['count'] == 1


def test_ontology_model():
    ontology = Ontology(
        ontology_source='dummy', ontology_id='chebi', metadata={'foo': 'bar'}
    )
    assert ontology.get_ontology() == 'dummy'
    assert ontology.get_ontology_id() == 'chebi'
    assert ontology.get_metadata() == {'foo': 'bar'}
