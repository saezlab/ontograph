from pathlib import Path
import tempfile

import pytest
import requests
import responses

from ontograph.downloader import DownloaderPort, PoochDownloaderAdapter

__all__ = [
    'MockCatalog',
    'TestDownloaderPort',
    'TestPoochDownloaderAdapter',
]


# Tests for DownloaderPort (Abstract Base Class)
class TestDownloaderPort:
    """Test suite for the abstract DownloaderPort class."""

    class ConcreteDownloader(DownloaderPort):
        """Concrete implementation of DownloaderPort for testing abstract class."""

        def fetch_from_url(
            self, url_ontology: str, filename: str | None
        ) -> Path:
            return Path('dummy/path')

        def fetch_from_catalog(
            self, resources: list[dict[str, str]], catalog
        ) -> dict[str, Path]:
            return {'dummy': Path('dummy/path')}

    def test_abstract_instantiation(self):
        """Test that DownloaderPort cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DownloaderPort()

    def test_concrete_instantiation(self):
        """Test that a concrete implementation can be instantiated."""
        concrete = self.ConcreteDownloader()
        assert isinstance(concrete, DownloaderPort)

    def test_abstract_methods_implementation(self):
        """Test that concrete implementation provides required methods."""
        concrete = self.ConcreteDownloader()
        assert hasattr(concrete, 'fetch_from_url')
        assert hasattr(concrete, 'fetch_from_catalog')

        # Test method calls
        result_path = concrete.fetch_from_url('http://example.com', 'test.owl')
        assert isinstance(result_path, Path)

        catalog_results = concrete.fetch_from_catalog(
            [{'name_id': 'test'}], None
        )
        assert isinstance(catalog_results, dict)


class MockCatalog:
    """Mock catalog class for testing."""

    def get_download_url(self, name_id: str, format_type: str) -> str:
        if name_id == 'missing':
            return None
        return f'http://example.com/{name_id}.{format_type}'


class TestPoochDownloaderAdapter:
    """Test suite for the PoochDownloaderAdapter class."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for test cache."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def downloader(self, temp_cache_dir):
        """Create a PoochDownloaderAdapter instance for testing."""
        return PoochDownloaderAdapter(cache_dir=temp_cache_dir)

    @pytest.fixture
    def mock_catalog(self):
        """Create a mock catalog for testing."""
        return MockCatalog()

    def test_initialization(self, downloader, temp_cache_dir):
        """Test that PoochDownloaderAdapter initializes correctly."""
        assert downloader._cache_dir == temp_cache_dir
        assert isinstance(downloader._resources_paths, dict)
        assert len(downloader._resources_paths) == 0
        assert temp_cache_dir.exists()

    def test_get_paths(self, downloader):
        """Test get_paths method returns resource paths dictionary."""
        paths = downloader.get_paths()
        assert isinstance(paths, dict)
        assert len(paths) == 0

        # Add a test path
        test_path = Path('test/path')
        downloader._resources_paths['test'] = test_path

        paths = downloader.get_paths()
        assert len(paths) == 1
        assert paths['test'] == test_path

    def test_validate_download_parameters(self, downloader):
        """Test parameter validation."""
        # Valid parameters
        downloader._validate_download_parameters(
            'http://example.com', 'test.owl'
        )

        # Empty URL
        with pytest.raises(ValueError, match='URL cannot be empty'):
            downloader._validate_download_parameters('', 'test.owl')

        # Whitespace URL
        with pytest.raises(ValueError, match='URL cannot be empty'):
            downloader._validate_download_parameters('   ', 'test.owl')

        # Empty filename
        with pytest.raises(ValueError, match='Filename cannot be empty'):
            downloader._validate_download_parameters('http://example.com', '')

        # Whitespace filename
        with pytest.raises(ValueError, match='Filename cannot be empty'):
            downloader._validate_download_parameters('http://example.com', '  ')

    @responses.activate
    def test_fetch_from_url(self, downloader, temp_cache_dir):
        """Test fetch_from_url method with mocked HTTP response."""
        test_url = 'http://example.com/test.owl'
        test_content = b'<owl>Test ontology content</owl>'
        test_filename = 'test.owl'

        # Mock HTTP response
        responses.add(responses.GET, test_url, body=test_content, status=200)

        # Call method
        result_path = downloader.fetch_from_url(test_url, test_filename)

        # Verify results
        assert isinstance(result_path, Path)
        assert result_path.exists()
        assert result_path.parent == temp_cache_dir
        assert result_path.name == test_filename

        # Check if added to resources paths
        assert 'test' in downloader._resources_paths
        assert downloader._resources_paths['test'] == result_path

    @responses.activate
    def test_fetch_from_url_request_exception(self, downloader):
        """Test fetch_from_url handles request exceptions correctly."""
        test_url = 'http://example.com/error.owl'
        test_filename = 'error.owl'

        # Mock HTTP error
        responses.add(responses.GET, test_url, status=404)

        # Call method and expect exception

        with pytest.raises(requests.RequestException):
            downloader.fetch_from_url(test_url, test_filename)

    def test_extract_resource_info(self, downloader):
        """Test _extract_resource_info extracts correct information."""
        # Test with name_id and format
        resource = {'name_id': 'go', 'format': 'owl'}
        name_id, format_type = downloader._extract_resource_info(resource)
        assert name_id == 'go'
        assert format_type == 'owl'

        # Test with name_id only (default format)
        resource = {'name_id': 'go'}
        name_id, format_type = downloader._extract_resource_info(resource)
        assert name_id == 'go'
        assert format_type == 'obo'  # Default format

        # Test with missing name_id
        resource = {'format': 'owl'}
        with pytest.raises(
            KeyError, match="Resource dictionary must contain 'name_id' key"
        ):
            downloader._extract_resource_info(resource)

    def test_get_resource_url(self, downloader, mock_catalog):
        """Test _get_resource_url retrieves correct URL from catalog."""
        # Valid resource
        url = downloader._get_resource_url('go', 'owl', mock_catalog)
        assert url == 'http://example.com/go.owl'

        # Missing resource
        with pytest.raises(
            ValueError, match='Cannot find download URL for ontology missing'
        ):
            downloader._get_resource_url('missing', 'owl', mock_catalog)

    @pytest.mark.parametrize(
        'resources',
        [
            [],
            None,
        ],
    )
    def test_fetch_from_catalog_empty(
        self, downloader, mock_catalog, resources
    ):
        """Test fetch_from_catalog with empty resources list."""
        with pytest.raises(
            ValueError, match='Resources list for batch download is empty.'
        ):
            downloader.fetch_from_catalog(resources, mock_catalog)

    @responses.activate
    def test_fetch_from_catalog(self, downloader, mock_catalog):
        """Test fetch_from_catalog with multiple resources."""
        resources = [
            {'name_id': 'go', 'format': 'obo'},
            {'name_id': 'ado', 'format': 'owl'},
        ]

        # Mock HTTP responses
        responses.add(
            responses.GET,
            'http://example.com/go.obo',
            body=b'GO ontology content',
            status=200,
        )
        responses.add(
            responses.GET,
            'http://example.com/ado.owl',
            body=b'ADO ontology content',
            status=200,
        )

        # Call method
        results = downloader.fetch_from_catalog(resources, mock_catalog)

        # Verify results
        assert len(results) == 2
        assert 'go' in results
        assert 'ado' in results
        assert results['go'].exists()
        assert results['ado'].exists()

        # Verify resources_paths is updated
        assert 'go' in downloader._resources_paths
        assert 'ado' in downloader._resources_paths
