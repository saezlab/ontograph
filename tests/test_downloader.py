"""Unit tests for the downloader module."""

from pathlib import Path
from dataclasses import dataclass

import pytest

from ontograph.downloader import PoochDownloaderAdapter
from ontograph.ontology_registry import OBORegistryAdapter

__all__ = [
    'DEFAULT_TEST_URL',
    'MockRegistry',
    'TEST_BASE_URL',
    'downloader',
    'mock_registry',
    'temp_cache_dir',
    'test_fetch_batch_default_format',
    'test_fetch_batch_empty_resources',
    'test_fetch_batch_missing_name_id',
    'test_fetch_batch_successful',
    'test_fetch_batch_url_not_found',
    'test_fetch_creates_file',
    'test_fetch_download_failure',
    'test_get_download_url_not_found',
    'test_get_download_url_success',
    'test_init_creates_cache_dir',
]

# Test constants
TEST_BASE_URL = 'http://example.com'
DEFAULT_TEST_URL = f'{TEST_BASE_URL}/test.obo'


@dataclass
class MockRegistry:
    """Mock implementation of OBORegistryAdapter."""

    url: str | None = DEFAULT_TEST_URL
    cache_dir: Path = Path('./mock_cache')

    def __post_init__(self) -> None:
        """Initialize mock registry."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_download_url(self, ontology_id: str, format: str = 'obo') -> str:
        """Mock URL resolution."""
        return self.url


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Provide temporary directory for testing."""
    return tmp_path


@pytest.fixture
def mock_registry(
    monkeypatch: pytest.MonkeyPatch, temp_cache_dir: Path
) -> MockRegistry:
    """Provide mock registry instance."""
    mock_reg = MockRegistry(cache_dir=temp_cache_dir)
    monkeypatch.setattr(OBORegistryAdapter, '__new__', lambda cls: mock_reg)
    return mock_reg


@pytest.fixture
def downloader(
    temp_cache_dir: Path, mock_registry: MockRegistry
) -> PoochDownloaderAdapter:
    """Provide configured downloader instance."""
    return PoochDownloaderAdapter(
        cache_dir=temp_cache_dir, registry=mock_registry
    )


def test_init_creates_cache_dir(
    temp_cache_dir: Path, mock_registry: MockRegistry
) -> None:
    """Test that initialization creates cache directory."""
    PoochDownloaderAdapter(cache_dir=temp_cache_dir, registry=mock_registry)
    assert temp_cache_dir.exists()
    assert temp_cache_dir.is_dir()


def test_get_download_url_success(downloader: PoochDownloaderAdapter) -> None:
    """Test successful URL resolution."""
    url = downloader._get_download_url('test', 'obo')
    assert url == DEFAULT_TEST_URL


def test_get_download_url_not_found(
    downloader: PoochDownloaderAdapter, mock_registry: MockRegistry
) -> None:
    """Test URL resolution when ontology not found."""
    mock_registry.url = None
    url = downloader._get_download_url('nonexistent', 'obo')
    assert url is None


def test_fetch_creates_file(
    monkeypatch: pytest.MonkeyPatch,
    downloader: PoochDownloaderAdapter,
    temp_cache_dir: Path,
) -> None:
    """Test that fetch creates a file in cache directory."""

    def mock_retrieve(
        url: str, known_hash: None, fname: str, path: Path, progressbar: bool
    ) -> str:
        file_path = path / fname
        file_path.touch()
        return str(file_path)

    monkeypatch.setattr('ontograph.downloader.retrieve', mock_retrieve)

    result = downloader.fetch(DEFAULT_TEST_URL, 'test.obo')
    assert result.exists()
    assert result.parent == temp_cache_dir


def test_fetch_download_failure(
    monkeypatch: pytest.MonkeyPatch, downloader: PoochDownloaderAdapter
) -> None:
    """Test handling of download failures."""

    def mock_retrieve(*args: object, **kwargs: object) -> None:
        raise Exception('Download failed')

    monkeypatch.setattr('ontograph.downloader.retrieve', mock_retrieve)

    with pytest.raises(Exception, match='Download failed'):
        downloader.fetch(DEFAULT_TEST_URL, 'test.obo')


def test_fetch_batch_empty_resources(
    downloader: PoochDownloaderAdapter,
) -> None:
    """Test fetch_batch with empty resource list."""
    with pytest.raises(
        ValueError, match='Resources list for batch download is empty.'
    ):
        downloader.fetch_batch([])


def test_fetch_batch_missing_name_id(
    downloader: PoochDownloaderAdapter,
) -> None:
    """Test fetch_batch with missing name_id in resource."""
    with pytest.raises(
        KeyError, match="Resource dictionary must contain 'name_id' key"
    ):
        downloader.fetch_batch([{'format': 'obo'}])


def test_fetch_batch_url_not_found(
    downloader: PoochDownloaderAdapter, mock_registry: MockRegistry
) -> None:
    """Test fetch_batch when URL cannot be resolved."""
    mock_registry.url = None
    resources = [{'name_id': 'test', 'format': 'obo'}]

    with pytest.raises(
        ValueError, match='Cannot find download URL for ontology test'
    ):
        downloader.fetch_batch(resources)


def test_fetch_batch_successful(
    monkeypatch: pytest.MonkeyPatch,
    downloader: PoochDownloaderAdapter,
    temp_cache_dir: Path,
) -> None:
    """Test successful batch download."""

    def mock_retrieve(
        url: str, known_hash: None, fname: str, path: Path, progressbar: bool
    ) -> str:
        file_path = path / fname
        file_path.touch()
        return str(file_path)

    monkeypatch.setattr('ontograph.downloader.retrieve', mock_retrieve)

    resources = [
        {'name_id': 'test1', 'format': 'obo'},
        {'name_id': 'test2', 'format': 'owl'},
    ]

    results = downloader.fetch_batch(resources)

    assert len(results) == 2
    assert all(isinstance(path, Path) for path in results.values())
    assert all(path.exists() for path in results.values())
    assert results['test1'].name == 'test1.obo'
    assert results['test2'].name == 'test2.owl'


def test_fetch_batch_default_format(
    monkeypatch: pytest.MonkeyPatch,
    downloader: PoochDownloaderAdapter,
    temp_cache_dir: Path,
) -> None:
    """Test fetch_batch with default format (obo)."""

    def mock_retrieve(
        url: str, known_hash: None, fname: str, path: Path, progressbar: bool
    ) -> str:
        file_path = path / fname
        file_path.touch()
        return str(file_path)

    monkeypatch.setattr('ontograph.downloader.retrieve', mock_retrieve)

    resources = [{'name_id': 'test'}]  # No format specified
    results = downloader.fetch_batch(resources)

    assert len(results) == 1
    assert results['test'].name == 'test.obo'  # Should use default 'obo' format
