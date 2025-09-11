"""This module provides utility functions for the ontograph library.

It includes functions for handling mapping files, such as reading delimited
files into pandas DataFrames and creating reverse mapping lookup tables (LUTs).
These utilities are essential for translating identifiers from different
databases to a unified format, which is a common requirement in bioinformatics
and ontology-related workflows.

The main functions provided are:
- `load_mapping_lut`: Orchestrates the process of reading a mapping file and
  generating a reverse mapping LUT.
- `translate_ids`: Translates a list of term IDs using a provided mapping LUT.

Internal helper functions like `_read_mapping_file` and `_create_reverse_mapping`
support the main functionality by handling file reading and the transformation
of data into the desired LUT format.
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# ------------------------------------------------------------
# ----  Utility functions for the mapping lookup table    ----
# ------------------------------------------------------------
def _read_mapping_file(filepath: str, delimiter: str) -> pd.DataFrame:
    r"""Reads a delimited file into a pandas DataFrame with all columns as strings.

    Args:
        filepath: The path to the mapping file.
        delimiter: The delimiter used in the file (e.g., '\\t').

    Returns:
        A pandas DataFrame containing the file's data.
    """
    try:
        dataframe = pd.read_table(
            filepath_or_buffer=filepath, delimiter=delimiter, dtype=str
        )
    except pd.errors.EmptyDataError as e:
        raise pd.errors.EmptyDataError(
            f'No columns to parse from file: {filepath}'
        ) from e
    return dataframe


def _create_reverse_mapping(
    dataframe: pd.DataFrame, target_column: str
) -> dict[str, str]:
    """Creates a reverse mapping dictionary (LUT) from a DataFrame.

    It transforms the DataFrame from a wide format to a long format, creating a
    many-to-one mapping from various source ID columns to a single target ID column.

    Args:
        dataframe: The DataFrame containing the ID mappings.
        target_column: The column name to map to (e.g., 'swiss_lipid_id').

    Returns:
        A dictionary where keys are IDs from source columns and values are from the target_column.
    """
    if dataframe.empty:
        return set(), {}

    if target_column not in dataframe.columns:
        raise KeyError(
            f"Target column '{target_column}' not found in DataFrame."
        )

    # Ensure we only work with rows that have a target ID
    df_filtered = dataframe.dropna(subset=[target_column])

    # Unpivot all columns except the target_column into a long format
    df_melted = df_filtered.melt(
        id_vars=[target_column],
        var_name='database_name',
        value_name='database_id',
    )

    databases_names = set(df_melted['database_name'].unique())

    # Drop any rows where the new 'database_id' column is empty
    df_melted.dropna(subset=['database_id'], inplace=True)

    # Create the mapping dictionary from the database_id and target_column.
    # This is a highly efficient, vectorized way to create the dictionary.
    reverse_map = pd.Series(
        df_melted[target_column].values, index=df_melted.database_id
    ).to_dict()

    return databases_names, reverse_map


def load_mapping_lut(
    filepath: str, delimiter: str, target_column: str
) -> dict[str, str]:
    """Loads a mapping file and creates a reverse mapping lookup table (LUT).

    This is the main public function that orchestrates reading the file and
    generating the LUT.

    Args:
        filepath: The path to the mapping file.
        delimiter: The delimiter used in the file.
        target_column: The name of the column containing the target IDs.

    Returns:
        A dictionary mapping various source IDs to the target IDs.
    """
    # Read tabular data
    dataframe = _read_mapping_file(filepath=filepath, delimiter=delimiter)

    # Generate Lookup Table
    databases_names, reverse_map = _create_reverse_mapping(
        dataframe=dataframe, target_column=target_column
    )

    return databases_names, reverse_map


# ------------------------------------------------------
# ----  Utility functions for transforming terms    ----
# ------------------------------------------------------
def translate_ids(
    mapping_lut: dict[str, str] | None, terms_id: list[str]
) -> list[str]:
    """Translates a list of term IDs using a mapping lookup table (LUT).

    If a term ID is already a valid target ID, it is returned as-is.
    If a term ID exists in the LUT, it is translated to the corresponding target ID.
    If a term ID cannot be translated, a warning is logged and it is skipped.

    Args:
        mapping_lut (dict[str, str] | None): The mapping lookup table. If None, terms are returned unchanged.
        terms_id (list[str]): List of term IDs to translate.

    Returns:
        list[str]: List of translated term IDs.
    """
    if mapping_lut is None or mapping_lut == {}:
        logger.warning('Warning: Mapping LUT is not available.')
        return terms_id

    target_values = set(mapping_lut.values())
    translated_terms: list[str] = []

    for term_id in terms_id:
        # Case 1: The term is already a valid target ID.
        if term_id in target_values:
            translated_terms.append(term_id)
            continue

        # Case 2: The term needs to be translated.
        translated = mapping_lut.get(term_id)

        if translated is not None:
            translated_terms.append(translated)
        else:
            # Case 3: The term is not a target ID and not in the LUT.
            logger.warning(
                f"Warning: Term '{term_id}' could not be translated."
            )

    return translated_terms
