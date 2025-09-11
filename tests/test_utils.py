import pandas as pd
import pytest

from ontograph.utils import _read_mapping_file


# ---- Pytest Fixtures
@pytest.fixture
def sample_mapping_file(tmp_path):
    """Create a sample mapping file for testing."""
    content = 'col1\tcol2\tcol3\n1\t2\t3\na\tb\tc'
    file_path = tmp_path / 'sample_mapping.tsv'
    file_path.write_text(content)
    return str(file_path)


@pytest.fixture
def empty_mapping_file(tmp_path):
    """Create an empty mapping file for testing."""
    file_path = tmp_path / 'empty_mapping.tsv'
    file_path.write_text('')
    return str(file_path)


@pytest.fixture
def csv_mapping_file(tmp_path):
    """Create a sample CSV mapping file for testing."""
    content = 'col1,col2,col3\n1,2,3\nd,e,f'
    file_path = tmp_path / 'sample_mapping.csv'
    file_path.write_text(content)
    return str(file_path)


# ---- Unit tests for _read_mapping_file
def test_read_mapping_file_valid(sample_mapping_file):
    """Test reading a valid mapping file."""
    df = _read_mapping_file(sample_mapping_file, delimiter='\t')
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    expected_columns = ['col1', 'col2', 'col3']
    assert all(col in df.columns for col in expected_columns)
    assert df.shape == (2, 3)


def test_read_mapping_file_non_existent():
    """Test reading a non-existent file."""
    with pytest.raises(FileNotFoundError):
        _read_mapping_file('non_existent_file.tsv', delimiter='\t')


def test_read_mapping_file_empty(empty_mapping_file):
    """Test reading an empty file."""
    with pytest.raises(pd.errors.EmptyDataError):
        _read_mapping_file(empty_mapping_file, delimiter='\t')


def test_read_mapping_file_different_delimiter(csv_mapping_file):
    """Test reading a file with a different delimiter."""
    df = _read_mapping_file(csv_mapping_file, delimiter=',')
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.shape == (2, 3)


def test_read_mapping_file_all_columns_are_strings(sample_mapping_file):
    """Test that all columns are read as strings."""
    df = _read_mapping_file(sample_mapping_file, delimiter='\t')
    for dtype in df.dtypes:
        assert pd.api.types.is_string_dtype(dtype)
