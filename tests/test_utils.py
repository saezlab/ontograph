import pandas as pd
import pytest

from ontograph.utils import (
    _create_reverse_mapping,
    _read_mapping_file,
)


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


@pytest.fixture
def well_formed_dataframe():
    """Create a well-formed DataFrame for testing."""
    data = {
        'target_id': ['T1', 'T2', 'T3'],
        'source_A': ['A1', 'A2', None],
        'source_B': ['B1', None, 'B3'],
    }
    return pd.DataFrame(data)


@pytest.fixture
def df_with_missing_target_ids():
    """Create a DataFrame with missing target IDs."""
    data = {
        'target_id': ['T1', None, 'T3'],
        'source_A': ['A1', 'A2', 'A3'],
        'source_B': ['B1', 'B2', 'B3'],
    }
    return pd.DataFrame(data)


@pytest.fixture
def empty_dataframe():
    """Create an empty DataFrame."""
    return pd.DataFrame()


@pytest.fixture
def df_with_duplicate_source_ids():
    """Create a DataFrame with duplicate source IDs."""
    data = {
        'target_id': ['T1', 'T2'],
        'source_A': ['A1', 'A1'],  # duplicate source ID
    }
    return pd.DataFrame(data)


@pytest.fixture
def df_with_only_target_column():
    """Create a DataFrame with only the target column."""
    data = {'target_id': ['T1', 'T2', 'T3']}
    return pd.DataFrame(data)


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


# ---- Unit tests for _create_reverse_mapping
def test_create_reverse_mapping_well_formed(well_formed_dataframe):
    """Test with a standard, well-formed DataFrame."""
    target_column = 'target_id'
    db_names, reverse_map = _create_reverse_mapping(
        well_formed_dataframe, target_column
    )

    expected_map = {'A1': 'T1', 'A2': 'T2', 'B1': 'T1', 'B3': 'T3'}
    expected_db_names = {'source_A', 'source_B'}

    assert db_names == expected_db_names
    assert reverse_map == expected_map


def test_create_reverse_mapping_missing_target_ids(df_with_missing_target_ids):
    """Test with missing target IDs."""
    target_column = 'target_id'
    db_names, reverse_map = _create_reverse_mapping(
        df_with_missing_target_ids, target_column
    )
    # The row with the missing target ID should be ignored
    expected_map = {'A1': 'T1', 'A3': 'T3', 'B1': 'T1', 'B3': 'T3'}
    assert reverse_map == expected_map


def test_create_reverse_mapping_empty_dataframe(empty_dataframe):
    """Test with an empty DataFrame."""
    target_column = 'target_id'
    db_names, reverse_map = _create_reverse_mapping(
        empty_dataframe, target_column
    )

    assert db_names == set()
    assert reverse_map == {}


def test_create_reverse_mapping_non_existent_target_column(
    well_formed_dataframe,
):
    """Test with a non-existent target column."""
    with pytest.raises(KeyError):
        _create_reverse_mapping(well_formed_dataframe, 'non_existent_column')


def test_create_reverse_mapping_duplicate_source_ids(
    df_with_duplicate_source_ids,
):
    """Test with duplicate source IDs mapping to different targets."""
    target_column = 'target_id'
    _, reverse_map = _create_reverse_mapping(
        df_with_duplicate_source_ids, target_column
    )
    # The last encountered mapping for 'A1' should be kept
    assert reverse_map['A1'] == 'T2'


def test_create_reverse_mapping_only_target_column(df_with_only_target_column):
    """Test with a DataFrame containing only the target column."""
    target_column = 'target_id'
    db_names, reverse_map = _create_reverse_mapping(
        df_with_only_target_column, target_column
    )

    assert db_names == set()
    assert reverse_map == {}
