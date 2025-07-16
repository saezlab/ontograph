"""Test module for the ontology_loader module.

This module contains tests for the ProntoLoaderAdapter class and its functionality
using pytest.
"""

from pathlib import Path

import pytest
from pronto.ontology import Ontology

from ontograph.config.settings import DEFAULT_CACHE_DIR
from ontograph.ontology_loader import ProntoLoaderAdapter

__all__ = [
    'mock_ontology_file',
    'temp_cache_dir',
    'test_init_with_custom_cache',
    'test_init_with_default_cache',
    'test_init_with_string_path',
    'test_load_invalid_format',
    'test_load_missing_file',
    'test_load_valid_ontology',
]


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Fixture to create a temporary cache directory.

    Args:
        tmp_path: Pytest fixture providing a temporary directory.

    Returns:
        Path: A Path object pointing to the temporary directory.
    """
    return tmp_path


@pytest.fixture
def mock_ontology_file(temp_cache_dir: Path) -> Path:
    """Fixture to create a mock ontology file.

    Args:
        temp_cache_dir: Fixture providing a temporary directory.

    Returns:
        Path: A Path object pointing to the created mock ontology file.
    """
    # Create a minimal OBO file for testing
    obo_content = """
    format-version: 1.2
    ontology: test

    [Term]
    id: TEST:001
    name: test term
    """
    test_file = temp_cache_dir / 'test.obo'
    test_file.write_text(obo_content)
    return test_file


# --------------------------
# ----    UNIT TESTS    ----
# --------------------------
def test_init_with_default_cache() -> None:
    """Test initialization with default cache directory."""
    loader = ProntoLoaderAdapter()
    assert loader.cache_dir == DEFAULT_CACHE_DIR
    assert loader.cache_dir.exists()


def test_init_with_custom_cache(temp_cache_dir: Path) -> None:
    """Test initialization with custom cache directory."""
    loader = ProntoLoaderAdapter(cache_dir=temp_cache_dir)
    assert loader.cache_dir == temp_cache_dir
    assert loader.cache_dir.exists()


def test_init_with_string_path() -> None:
    """Test initialization with string path."""
    path_str = './test_cache'
    loader = ProntoLoaderAdapter(cache_dir=path_str)
    assert loader.cache_dir == Path(path_str)
    assert loader.cache_dir.exists()
    # Cleanup
    loader.cache_dir.rmdir()


def test_load_invalid_format(temp_cache_dir: Path) -> None:
    """Test loading with invalid format."""
    loader = ProntoLoaderAdapter(cache_dir=temp_cache_dir)
    with pytest.raises(ValueError, match='Unsupported format: invalid'):
        loader.load('test', format='invalid')


def test_load_missing_file(temp_cache_dir: Path) -> None:
    """Test loading a non-existent file."""
    loader = ProntoLoaderAdapter(cache_dir=temp_cache_dir)
    with pytest.raises(FileNotFoundError):
        loader.load('nonexistent', format='obo')


def test_load_valid_ontology(
    temp_cache_dir: Path, mock_ontology_file: Path
) -> None:
    """Test loading a valid ontology file."""
    loader = ProntoLoaderAdapter(cache_dir=temp_cache_dir)
    ontology = loader.load('test', format='obo')
    assert isinstance(ontology, Ontology)
    assert len(ontology.terms()) > 0
