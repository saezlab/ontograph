"""Test module for the downloader module functionality."""

from pathlib import Path
import pytest
from unittest.mock import Mock

from ontograph.downloader import PoochDownloaderAdapter
from ontograph.ontology_registry import OBORegistryAdapter


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create temp directory for testing."""
    return tmp_path


# Change fixtures to use monkeypatch
@pytest.fixture
def mock_registry(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Create a mock registry for testing."""
    registry = Mock(spec=OBORegistryAdapter)
    registry.get_download_url.return_value = "http://example.com/test.obo"
    return registry


@pytest.fixture
def downloader(temp_cache_dir: Path, mock_registry: Mock) -> PoochDownloaderAdapter:
    """Create a PoochDownloaderAdapter instance for testing."""
    return PoochDownloaderAdapter(cache_dir=temp_cache_dir, registry=mock_registry)


def test_init(temp_cache_dir: Path, mock_registry: Mock) -> None:
    """Test downloader initialization."""
    downloader = PoochDownloaderAdapter(cache_dir=temp_cache_dir, registry=mock_registry)
    assert downloader.cache_dir == temp_cache_dir
    assert downloader.registry == mock_registry
    assert temp_cache_dir.exists()


def test_get_download_url(downloader: PoochDownloaderAdapter) -> None:
    """Test internal URL resolution."""
    url = downloader._get_download_url("test", "obo")
    assert url == "http://example.com/test.obo"
    downloader.registry.get_download_url.assert_called_once_with("test", "obo")


def test_fetch_with_nonexistent_url(
    monkeypatch: pytest.MonkeyPatch, downloader: PoochDownloaderAdapter
) -> None:
    """Test fetch with non-existent URL."""
    mock_retrieve = Mock(side_effect=Exception("Failed to download"))
    monkeypatch.setattr("ontograph.downloader.retrieve", mock_retrieve)

    with pytest.raises(Exception, match="Failed to download"):
        downloader.fetch("http://nonexistent.com/test.obo", "test.obo")


def test_fetch_with_invalid_filename(
    mocker: MockFixture, downloader: PoochDownloaderAdapter
) -> None:
    """Test fetch with invalid filename."""
    mock_retrieve = mocker.patch("ontograph.downloader.retrieve")
    mock_retrieve.side_effect = ValueError("Invalid filename")

    with pytest.raises(ValueError, match="Invalid filename"):
        downloader.fetch("http://example.com/test.obo", "")


def test_fetch_batch_mixed_success(
    mocker: MockFixture,
    downloader: PoochDownloaderAdapter,
    mock_registry: MockFixture,
    temp_cache_dir: Path,
) -> None:
    """Test batch download with some successes and failures."""
    resources = [
        {"name_id": "success", "format": "obo"},
        {"name_id": "fail", "format": "owl"},
    ]

    mock_registry.get_download_url.side_effect = ["http://example.com/success.obo", None]

    with pytest.raises(ValueError, match="Cannot find download URL for ontology fail"):
        downloader.fetch_batch(resources)


def test_fetch_batch_empty_resources(
    downloader: PoochDownloaderAdapter,
) -> None:
    """Test fetch_batch with empty resources list."""
    with pytest.raises(ValueError, match="Resources list for batch download is empty."):
        downloader.fetch_batch([])


def test_fetch_batch_missing_name_id(
    downloader: PoochDownloaderAdapter,
) -> None:
    """Test fetch_batch with missing name_id in resource."""
    resources: list[dict[str, str]] = [{"format": "obo"}]  # Missing name_id
    with pytest.raises(KeyError, match="Resource dictionary must contain 'name_id' key"):
        downloader.fetch_batch(resources)


def test_fetch_batch_invalid_ontology(
    downloader: PoochDownloaderAdapter, mock_registry: MockFixture
) -> None:
    """Test fetch_batch with invalid ontology ID."""
    mock_registry.get_download_url.return_value = None

    resources: list[dict[str, str]] = [{"name_id": "invalid", "format": "obo"}]
    with pytest.raises(ValueError, match="Cannot find download URL for ontology invalid"):
        downloader.fetch_batch(resources)


def test_fetch_batch_successful(
    mocker: MockFixture,
    downloader: PoochDownloaderAdapter,
    temp_cache_dir: Path,
    mock_registry: MockFixture,
) -> None:
    """Test successful batch download of multiple ontologies."""
    resources: list[dict[str, str]] = [
        {"name_id": "go", "format": "obo"},
        {"name_id": "chebi", "format": "owl"},
    ]

    mock_registry.get_download_url.side_effect = [
        "http://example.com/go.obo",
        "http://example.com/chebi.owl",
    ]

    mock_retrieve = mocker.patch("ontograph.downloader.retrieve")
    mock_retrieve.side_effect = [
        str(temp_cache_dir / "go.obo"),
        str(temp_cache_dir / "chebi.owl"),
    ]

    results = downloader.fetch_batch(resources)

    assert len(results) == 2
    assert isinstance(results["go"], Path)
    assert isinstance(results["chebi"], Path)
    assert str(results["go"]) == str(temp_cache_dir / "go.obo")
    assert str(results["chebi"]) == str(temp_cache_dir / "chebi.owl")

    assert mock_registry.get_download_url.call_count == 2
    assert mock_retrieve.call_count == 2


def test_fetch_batch_default_format(
    downloader: PoochDownloaderAdapter, mock_registry: MockFixture
) -> None:
    """Test fetch_batch with default format (obo)."""
    # Setup test data
    resources = [{"name_id": "go"}]  # No format specified

    # Mock the fetch method to avoid actual downloads
    downloader.fetch = Mock(return_value=Path("test.obo"))

    # Call fetch_batch
    results = downloader.fetch_batch(resources)

    # Verify the default format was used
    mock_registry.get_download_url.assert_called_once_with("go", "obo")
    assert "go" in results
