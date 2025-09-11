import pandas as pd
import pytest

from ontograph.utils import (
    _create_reverse_mapping,
    _read_mapping_file,
    load_mapping_lut,
    translate_ids,
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


# ---- Unit tests for load_mapping_lut
def test_load_mapping_lut_success(sample_mapping_file):
    """Test loading a well-formed mapping file and generating the LUT."""
    delimiter = '\t'
    target_column = 'col1'
    databases_names, reverse_map = load_mapping_lut(
        filepath=sample_mapping_file,
        delimiter=delimiter,
        target_column=target_column,
    )

    # The file: col1\tcol2\tcol3\n1\t2\t3\na\tb\tc
    # Should produce:
    # databases_names: {'col2', 'col3'}
    # reverse_map: {'2': '1', '3': '1', 'b': 'a', 'c': 'a'}
    expected_db_names = {'col2', 'col3'}
    expected_reverse_map = {'2': '1', '3': '1', 'b': 'a', 'c': 'a'}

    assert databases_names == expected_db_names
    assert reverse_map == expected_reverse_map


def test_load_mapping_lut_file_not_found():
    """Test that FileNotFoundError is raised for a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_mapping_lut(
            filepath='non_existent_file.tsv',
            delimiter='\t',
            target_column='col1',
        )


def test_load_mapping_lut_empty_file(empty_mapping_file):
    """Test that EmptyDataError is raised for an empty file."""
    with pytest.raises(pd.errors.EmptyDataError):
        load_mapping_lut(
            filepath=empty_mapping_file, delimiter='\t', target_column='col1'
        )


def test_load_mapping_lut_non_existent_target_column(sample_mapping_file):
    """Test that KeyError is raised for a non-existent target column."""
    with pytest.raises(KeyError):
        load_mapping_lut(
            filepath=sample_mapping_file,
            delimiter='\t',
            target_column='non_existent_col',
        )


def test_load_mapping_lut_incorrect_delimiter(sample_mapping_file):
    """Test that KeyError is raised when delimiter is incorrect (columns not parsed)."""
    # Using comma delimiter on a tab-separated file will result in a single column
    with pytest.raises(KeyError):
        load_mapping_lut(
            filepath=sample_mapping_file, delimiter=',', target_column='col1'
        )


@pytest.fixture
def header_only_mapping_file(tmp_path):
    """Create a mapping file with only a header row."""
    content = 'col1\tcol2\tcol3\n'
    file_path = tmp_path / 'header_only_mapping.tsv'
    file_path.write_text(content)
    return str(file_path)


def test_load_mapping_lut_file_with_only_header(header_only_mapping_file):
    """Test with a mapping file containing only the header row."""
    databases_names, reverse_map = load_mapping_lut(
        filepath=header_only_mapping_file, delimiter='\t', target_column='col1'
    )
    # No data rows, so should be empty
    assert databases_names == set()
    assert reverse_map == {}


@pytest.fixture
def duplicate_source_mapping_file(tmp_path):
    """Create a mapping file with duplicate source IDs mapping to different targets."""
    content = 'target_id\tsource_A\nT1\tA1\nT2\tA1\n'
    file_path = tmp_path / 'duplicate_source_mapping.tsv'
    file_path.write_text(content)
    return str(file_path)


def test_load_mapping_lut_duplicate_source_ids(duplicate_source_mapping_file):
    """Test that the last mapping for a duplicate source ID is kept."""
    databases_names, reverse_map = load_mapping_lut(
        filepath=duplicate_source_mapping_file,
        delimiter='\t',
        target_column='target_id',
    )
    # The last mapping for 'A1' should be 'T2'
    assert databases_names == {'source_A'}
    assert reverse_map == {'A1': 'T2'}


# ---- Unit tests for translate_ids
def test_translate_ids_with_valid_lut_and_terms():
    """Test that terms present in the LUT are correctly translated to their target IDs."""
    mapping_lut = {'A1': 'T1', 'A2': 'T2', 'B1': 'T1', 'B3': 'T3'}
    terms_id = ['A1', 'A2', 'B1', 'B3']
    expected = ['T1', 'T2', 'T1', 'T3']
    result = translate_ids(mapping_lut, terms_id)
    assert result == expected


def test_translate_ids_with_mixed_terms():
    """Test that target IDs remain unchanged and source IDs are translated."""
    mapping_lut = {'A1': 'T1', 'A2': 'T2'}
    terms_id = ['A1', 'T1', 'A2', 'T2']
    expected = ['T1', 'T1', 'T2', 'T2']
    result = translate_ids(mapping_lut, terms_id)
    assert result == expected


def test_translate_ids_with_untranslatable_terms():
    """Test that untranslatable terms are skipped."""
    mapping_lut = {'A1': 'T1', 'A2': 'T2'}
    terms_id = ['A1', 'A2', 'X1', 'Y2']
    expected = ['T1', 'T2']
    result = translate_ids(mapping_lut, terms_id)
    assert result == expected


def test_translate_ids_with_none_lut():
    """Test that if LUT is None, input terms are returned unchanged."""
    terms_id = ['A1', 'A2', 'T1']
    expected = ['A1', 'A2', 'T1']
    result = translate_ids(None, terms_id)
    assert result == expected


def test_translate_ids_with_empty_lut():
    """Test that only valid target IDs are returned when LUT is empty."""
    mapping_lut = {}
    terms_id = ['T1', 'A1', 'T2']
    expected = ['T1', 'A1', 'T2']
    result = translate_ids(mapping_lut, terms_id)
    assert result == expected


def test_translate_ids_with_empty_terms():
    """Test that an empty input list returns an empty list."""
    mapping_lut = {'A1': 'T1'}
    terms_id = []
    expected = []
    result = translate_ids(mapping_lut, terms_id)
    assert result == expected


def test_translate_ids_with_duplicate_terms():
    """Test that duplicate terms are handled correctly and order is preserved."""
    mapping_lut = {'A1': 'T1', 'A2': 'T2'}
    terms_id = ['A1', 'A1', 'A2', 'A1']
    expected = ['T1', 'T1', 'T2', 'T1']
    result = translate_ids(mapping_lut, terms_id)
    assert result == expected
