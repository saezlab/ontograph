import re
import pprint
import logging
from pathlib import Path
from dataclasses import dataclass

from tqdm import tqdm
import yaml
import numpy as np
from pooch import retrieve
import pandas as pd
import pronto
import graphblas as gb

from ontograph.config.settings import (
    DEFAULT_CACHE_DIR,
    NAME_OBO_FOUNDRY_CATALOG,
    OBO_FOUNDRY_REGISTRY_URL,
)

__all__ = ['CatalogOntologies', 'Ontology']

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# ---------------------------------------------------------------- #
# --------- CLASSES related to the catalog of ontologies --------- #
# ---------------------------------------------------------------- #
class CatalogOntologies:
    """Manages the OBO Foundry catalog of ontologies.

    Provides methods to download, load, and query the ontology registry.
    """

    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR) -> None:
        """Initialize the catalog manager.

        Args:
            cache_dir (Path): Directory for caching registry files.
        """
        self.cache_dir = cache_dir
        self._catalog: dict | None = None

        # Create cache directory if this one doesn't exist.
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _download_registry(self) -> Path:
        """Download the latest catalog file.

        Returns:
            Path: Path to the downloaded catalog file.
        """
        catalog_path = self.cache_dir / NAME_OBO_FOUNDRY_CATALOG
        retrieve(
            url=OBO_FOUNDRY_REGISTRY_URL,
            known_hash=None,
            fname=NAME_OBO_FOUNDRY_CATALOG,
            path=self.cache_dir,
        )
        return catalog_path

    def load_catalog(self, force_download: bool = False) -> None:
        """Load the ontology catalog from disk or download if needed.

        Args:
            force_download (bool): If True, force download the catalog file.
        """
        catalog_path = self.cache_dir / NAME_OBO_FOUNDRY_CATALOG

        if force_download or not catalog_path.exists():
            catalog_path = self._download_registry()

        with open(catalog_path) as f:
            self._catalog = yaml.safe_load(f)

        return None

    @property
    def catalog(self) -> dict:
        """Return the loaded catalog as a dictionary.

        Returns:
            dict: The loaded catalog.
        """
        if self._catalog is None:
            self.load_catalog()
        return self._catalog

    def list_available_ontologies(self) -> list[dict]:
        """List available ontologies with their IDs and titles.

        Returns:
            list[dict]: List of ontologies with 'id' and 'title'.
        """
        list_ontologies = [
            {
                'id': ont.get('id'),
                'title': ont.get('title'),
            }
            for ont in self.catalog.get('ontologies', [])
            if ont.get('id')  # Only include if it has an ID
        ]

        return list_ontologies

    def print_available_ontologies(self) -> None:
        """Print the available ontologies in a formatted table."""
        list_ontologies = self.list_available_ontologies()

        print('{:<20} {:<40}'.format('name ID', 'Description'))
        print('-' * 60)

        for ontology in list_ontologies:
            print(
                '{:<20} {:<40}'.format(
                    ontology.get('id', ''), ontology.get('title', '')
                )
            )

    def print_catalog_schema_tree(self) -> None:
        """Print the schema structure of the OBO Foundry registry."""

        def _print_tree(
            data: list | dict, prefix: str = '', is_last: bool = True
        ) -> None:
            branch = '└── ' if is_last else '├── '
            child_prefix = prefix + ('    ' if is_last else '│   ')

            if isinstance(data, dict):
                for key in data.keys():
                    value = data[key]
                    print(f'{prefix}{branch}{key}')
                    if isinstance(value, dict):
                        _print_tree(value, child_prefix, True)
                    elif isinstance(value, list):
                        print(f'{child_prefix}└── [list]')
                        if value:
                            _print_tree(value[0], child_prefix + '    ', True)
            elif isinstance(data, list) and data:
                _print_tree(data[0], prefix, True)

        print('\nOBO Foundry Registry Schema Structure:\n')
        _print_tree(self.catalog)

        return None

    def get_ontology_metadata(
        self,
        ontology_id: str,
        show_metadata: bool = False,
    ) -> dict:
        """Retrieve metadata for a specific ontology.

        Args:
            ontology_id (str): Ontology identifier.
            show_metadata (bool): If True, pretty-print the metadata.

        Returns:
            dict: Metadata dictionary for the ontology.

        Raises:
            Exception: If metadata is not found.
        """
        try:
            for ontology in self.catalog.get('ontologies', []):
                if ontology.get('id') == ontology_id:
                    if show_metadata:
                        pprint.pprint(ontology)
                    return ontology
        except Exception as e:
            logger.exception(f'Metadata not found!: {e}')
            raise

    def get_download_url(
        self,
        ontology_id: str,
        format: str = 'obo',
    ) -> str:
        """Retrieve the download URL for a specific ontology and format.

        Args:
            ontology_id (str): Identifier of the ontology.
            format (str): Desired ontology file format (default: 'obo').

        Returns:
            str: The download URL (ontology_purl).

        Raises:
            ValueError: If the ontology or the specified format is not found in the catalog.
        """
        metadata = self.get_ontology_metadata(ontology_id, show_metadata=False)
        if metadata is None:
            raise ValueError(
                f"No metadata found for ontology ID '{ontology_id}'."
            )

        expected_id = f'{ontology_id.lower()}.{format.lower()}'
        products = metadata.get('products', [])

        for product in products:
            if product.get('id', '').lower() == expected_id:
                purl = product.get('ontology_purl')
                if purl:
                    return purl
                break  # Matching ID found but no URL

        raise ValueError(
            f"Download URL not found for ontology '{ontology_id}' with format '.{format}'."
        )

    def get_available_formats(self, ontology_id: str) -> list[str]:
        """Get available formats for a given ontology.

        Args:
            ontology_id (str): Ontology identifier.

        Returns:
            list[str]: List of available formats.
        """
        metadata = self.get_ontology_metadata(ontology_id)
        if not metadata:
            print(f'The metadata associated to {ontology_id} does not exist!')
            return []

        formats = set()

        for product in metadata.get('products', []):
            if product.get('id'):
                formats.add(product['id'].lower())

        return list(formats)


# ---------------------------------------------------------------- #
# ---------         CLASSES related to Ontologies        --------- #
# ---------------------------------------------------------------- #
class Ontology:
    """Represents an ontology loaded from a source."""

    def __init__(
        self,
        ontology_source: object,
        *,
        ontology_id: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Initialize the Ontology object.

        Args:
            ontology_source (Any): The loaded ontology object.
            ontology_id (str | None, optional): Ontology identifier.
            metadata (dict | None, optional): Metadata dictionary.
        """
        self._ontology = ontology_source
        self._ontology_id = ontology_id
        self._metadata = metadata

    def get_ontology(self) -> object:
        """Return the underlying ontology object.

        Returns:
            Any: The loaded ontology object.
        """
        return self._ontology

    def get_ontology_id(self) -> str | None:
        """Return the ontology identifier.

        Returns:
            str | None: The ontology ID.
        """
        return self._ontology_id

    def get_metadata(self) -> dict | None:
        """Return the ontology metadata.

        Returns:
            dict | None: The metadata dictionary.
        """
        return self._metadata


# ---------------------------------------------------------------- #
# ---------          CLASSES related to Graphs           --------- #
# ---------------------------------------------------------------- #


class LookUpTables:
    def __init__(self, terms: list) -> None:
        self.__lut_term_to_index: dict[str, int] = {
            term.id: idx for idx, term in enumerate(terms)
        }
        self.__lut_index_to_term: list[str] = [term.id for term in terms]
        self.__lut_term_to_description: dict[str, str] = {
            term.id: term.name for term in terms
        }
        self.__lut_description_to_term: dict[str, str] = {
            term.name: term.id for term in terms
        }

    def get_lut_term_to_index(self) -> dict[str, int]:
        return self.__lut_term_to_index

    def get_lut_index_to_term(self) -> list[str]:
        return self.__lut_index_to_term

    def get_lut_term_to_description(self) -> dict[str, str]:
        return self.__lut_term_to_description

    def get_lut_description_to_term(self) -> dict[str, str]:
        return self.__lut_description_to_term

    def term_to_index(self, terms: str | list) -> int | list:
        if isinstance(terms, str):
            return self.__lut_term_to_index[terms]
        elif isinstance(terms, list):
            return [self.__lut_term_to_index[term] for term in terms]

    def index_to_term(self, indexes: int | list) -> str | list:
        if isinstance(indexes, int):
            return self.__lut_index_to_term[indexes]
        elif isinstance(indexes, list):
            return [self.__lut_index_to_term[idx] for idx in indexes]
        elif isinstance(indexes, np.ndarray):
            return [self.__lut_index_to_term[idx] for idx in indexes.tolist()]
        else:
            raise TypeError(
                f'Expected int, list[int], or np.ndarray, got {type(indexes).__name__}.'
            )

    def term_to_description(self, terms: str | list) -> str | list:
        if isinstance(terms, str):
            return self.__lut_term_to_description[terms]
        elif isinstance(terms, list):
            return [self.__lut_term_to_description[term] for term in terms]

    def description_to_term(self, descriptions: str | list) -> str | list:
        if isinstance(descriptions, str):
            return self.__lut_description_to_term[descriptions]
        elif isinstance(descriptions, list):
            return [
                self.__lut_description_to_term[term] for term in descriptions
            ]


@dataclass
class NodeContainer:
    nodes_indices: np.ndarray

    def __len__(self) -> int:
        return len(self.nodes_indices)

    def __getitem__(self, idx: int) -> int | np.ndarray:
        return self.nodes_indices[idx]

    def as_list(self) -> list:
        return self.nodes_indices.tolist()

    def as_set(self) -> set:
        return set(self.nodes_indices)

    def __contains__(self, item: int) -> bool:
        return item in self.nodes_indices


class NodesDataframe:
    def __init__(self, terms: list, include_obsolete: bool = False) -> None:
        self.dataframe = self.create_nodes_dataframe(
            terms, include_obsolete=include_obsolete
        )

    def get_dataframe(self) -> pd.DataFrame:
        return self.dataframe

    # Function to split a string by multiple separators and get the last part
    def __get_last_part_string(
        self, s: str, separators: tuple = ('/', ':', '.', '#')
    ) -> str:
        # Create a regex pattern to split by any of the separators
        pattern = '|'.join(map(re.escape, separators))
        parts = re.split(pattern, s)

        return parts[-1] if parts else s

    def __get_dictitionary_annotations(self, annotations: object) -> dict:
        ann_dict = {}
        for annotation in annotations:
            # Get "annotation.property"
            key = self.__get_last_part_string(annotation.property)

            # Get elements from ResourcePropertyValue annotations
            if isinstance(annotation, pronto.ResourcePropertyValue):
                ann_dict[key] = {'resource': annotation.resource}
                continue

            # Get elements from LiteralPropertyValue annotations
            elif isinstance(annotation, pronto.LiteralPropertyValue):
                ann_dict[key] = {
                    'literal': annotation.literal,
                    'datatype': self.__get_last_part_string(
                        annotation.datatype
                    ),
                }
        return ann_dict

    def __get_string_relationships(self, relations: pronto.Relationship) -> str:
        rel_list = [relation.name for relation in relations.keys()]
        return ('|').join(rel_list)

    def __get_dictionary_synonyms(self, synonyms: pronto.synonym) -> dict:
        syn_dict = {}
        for synonym in synonyms:
            entry = {
                k: v
                for k, v in [
                    (
                        'type',
                        getattr(synonym.type, 'id', None)
                        if synonym.type
                        else None,
                    ),
                    (
                        'source',
                        '|'.join(str(source.id) for source in synonym.xrefs)
                        if synonym.xrefs
                        else None,
                    ),
                    (
                        'scope',
                        synonym.scope if synonym.scope is not None else None,
                    ),
                ]
                if v is not None and v != ''
            }
            syn_dict[synonym.description] = entry
        return syn_dict

    def __get_dictionary_xrefs(self, xrefs: pronto.Xref) -> dict:
        xref_dict = {}
        for xref in xrefs:
            entry = {
                k: v
                for k, v in [
                    (
                        'description',
                        xref.description if xref.description else None,
                    )
                ]
                if v is not None and v != ''
            }
            xref_dict[f'{xref.id}'] = entry
        return xref_dict

    def create_nodes_dataframe(
        self, terms: list, include_obsolete: bool = False
    ) -> pd.DataFrame:
        """Create a DataFrame with fields: ID, Name, Definition, Namespace, Subsets, Synonyms, Xrefs."""
        # Pre-bind functions for efficiency
        join = '|'.join
        str_ = str
        get_ann = self.__get_dictitionary_annotations
        get_syn = self.__get_dictionary_synonyms
        get_xref = self.__get_dictionary_xrefs
        get_rel = self.__get_string_relationships

        # Collect data for each term
        rows = []
        for term in tqdm(terms, desc='Building node dataframe', unit='term'):
            if not include_obsolete and term.obsolete:
                continue

            rows.append(
                {
                    'term_id': term.id,
                    'name': term.name,
                    'alternate_ids': join(term.alternate_ids)
                    if term.alternate_ids
                    else None,
                    'namespace': term.namespace,
                    'obsolete': term.obsolete,
                    'anonymous': term.anonymous,
                    'builtin': term.builtin,
                    'created_by': term.created_by,
                    'creation_date': term.creation_date,
                    'replaced_by': join([r.id for r in term.replaced_by])
                    if term.replaced_by
                    else None,
                    'consider': join(term.consider) if term.consider else None,
                    'definition': str_(term.definition)
                    if term.definition
                    else None,
                    'comment': term.comment,
                    'annotations': str(get_ann(term.annotations))
                    if term.annotations
                    else None,
                    'subsets': join(term.subsets) if term.subsets else None,
                    'synonyms': str(get_syn(term.synonyms))
                    if term.synonyms
                    else None,
                    'xrefs': str(get_xref(term.xrefs)) if term.xrefs else None,
                    'relationships': get_rel(term.relationships)
                    if term.relationships
                    else None,
                    'disjoint_from': term.disjoint_from
                    if term.disjoint_from
                    else None,
                    'equivalent_to': term.equivalent_to
                    if term.equivalent_to
                    else None,
                    'intersection_of': term.intersection_of
                    if term.intersection_of
                    else None,
                }
            )

        # Create DataFrame
        df = pd.DataFrame(rows)

        # Sort by term_id and reset index
        df.sort_values('term_id', inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Add index column
        df.insert(0, 'index', range(len(df)))

        return df

    # --- Refactored EdgesContainer: does NOT store terms ---


class EdgesContainer:
    def __init__(self, terms: list, lookup_tables: LookUpTables) -> None:
        self.edges_indices = self._populate_index_containers(
            terms, lookup_tables
        )
        self.relations = list(self.edges_indices.keys())

    # Search all possible relations in the ontology
    def _get_ontology_relationships(self, terms: list) -> list:
        set_relations = set()
        for term in terms:
            for rel in term.relationships:
                rel_name = rel.name.lower().replace(' ', '_')
                set_relations.add(rel_name)
        return sorted(set_relations)

    # Create empty containers for each relation type
    def _create_edges_index_containers(self, terms: list) -> dict:
        relationships = self._get_ontology_relationships(terms)

        # Always include 'is_a' relationship
        relationships.append('is_a')
        edge_container = {
            rel: {'rows': [], 'cols': []} for rel in relationships
        }
        return edge_container

    # Populate the containers with row and column indices
    def _populate_index_containers(
        self, terms: list, lookup_tables: LookUpTables
    ) -> dict:
        edge_container = self._create_edges_index_containers(terms)
        for term in tqdm(terms, desc='Building edge containers', unit='term'):
            # Populate 'is_a' relationships
            for subclass in term.subclasses(with_self=False, distance=1):
                if subclass.obsolete:
                    continue
                rel_name = 'is_a'
                edge_container[rel_name]['rows'].append(
                    lookup_tables.term_to_index(subclass.id)
                )
                edge_container[rel_name]['cols'].append(
                    lookup_tables.term_to_index(term.id)
                )

            # Populate other relationships
            for rel, targets in term.relationships.items():
                rel_name = rel.name.lower().replace(' ', '_')
                for target in targets:
                    if target.obsolete:
                        continue
                    edge_container[rel_name]['rows'].append(
                        lookup_tables.term_to_index(term.id)
                    )
                    edge_container[rel_name]['cols'].append(
                        lookup_tables.term_to_index(target.id)
                    )

        # Convert lists to numpy arrays with dtype np.int64
        for _rel, data in edge_container.items():
            data['rows'] = np.array(data['rows'], dtype=np.int64)
            data['cols'] = np.array(data['cols'], dtype=np.int64)
        return edge_container


class EdgesDataframe:
    def __init__(
        self, terms: pronto.Term, include_obsolete: bool = False
    ) -> None:
        self.dataframe = self.create_edges_dataframe(
            terms, include_obsolete=include_obsolete
        )

    def __get_last_part_string(
        self, input_string: str, separators: tuple = ('/', ':', '.', '#')
    ) -> str:
        pattern = '|'.join(map(re.escape, separators))
        parts = re.split(pattern, input_string)
        return parts[-1] if parts else input_string

    def create_edges_dataframe(
        self, terms: list, include_obsolete: bool = False
    ) -> 'pd.DataFrame':
        """Create a DataFrame with fields: source_id, source_name, relation, target_id, target_name, is_obsolete."""
        rows = []
        for term in tqdm(terms, desc='Building edge dataframe', unit='term'):
            if not include_obsolete and term.obsolete:
                continue
            source_id = term.id
            source_name = term.name
            for rel, targets in term.relationships.items():
                rel_name = rel.name
                for target in targets:
                    rows.append(
                        {
                            'source_id': source_id,
                            'source_name': source_name,
                            'relation': rel_name,
                            'target_id': target.id,
                            'target_name': target.name,
                            'is_obsolete': target.obsolete,
                        }
                    )
            # Add is_a relationships (subclasses)
            for subclass in term.subclasses(with_self=False, distance=1):
                if not include_obsolete and subclass.obsolete:
                    continue
                rows.append(
                    {
                        'source_id': subclass.id,
                        'source_name': subclass.name,
                        'relation': 'is_a',
                        'target_id': term.id,
                        'target_name': term.name,
                        'is_obsolete': subclass.obsolete,
                    }
                )

        df = pd.DataFrame(rows)
        df.sort_values(['source_id', 'relation', 'target_id'], inplace=True)
        df.reset_index(drop=True, inplace=True)
        df.insert(0, 'index', range(len(df)))
        return df


class Graph:
    def __init__(
        self,
        nodes_indexes: object,
        nodes_dataframe: object,
        edges_indexes: object,
        edges_dataframe: object,
        lookup_tables: object,
    ) -> None:
        # --- Nodes ---
        self.nodes_indexes = nodes_indexes
        self.nodes_dataframe = nodes_dataframe
        # --- Edges ---
        self.edges_indexes = edges_indexes
        self.edges_dataframe = edges_dataframe

        # --- Lookup Tables ---
        self.lookup_tables = lookup_tables
        self.number_nodes = len(self.nodes_indexes)
        self.number_edges = len(
            self.edges_indexes.edges_indices['is_a']['rows']
        )

        self.matrices_container = self.create_multiple_matrices(
            edge_container=self.edges_indexes.edges_indices,
            nrows=self.number_nodes,
            ncols=self.number_nodes,
        )

    def create_graphblas_matrix(
        self,
        rows_indexes: list,
        cols_indexes: list,
        nrows: int,
        ncols: int,
        name: str,
    ) -> object:
        M = gb.Matrix.from_coo(
            rows=rows_indexes,
            columns=cols_indexes,
            values=1.0,
            nrows=nrows,
            ncols=ncols,
            dtype=bool,
            name=name,
        )
        return M

    def create_multiple_matrices(
        self, edge_container: dict, nrows: int, ncols: int
    ) -> dict:
        matrices = {}
        for relation, indexes in edge_container.items():
            M = self.create_graphblas_matrix(
                rows_indexes=indexes['rows'],
                cols_indexes=indexes['cols'],
                nrows=nrows,
                ncols=ncols,
                name=relation,
            )

            matrices[relation] = M
        return matrices


class TermList(list):
    def __init__(self, term_ids: list, lookup_tables: object) -> None:
        super().__init__(term_ids)
        self._lookup_tables = lookup_tables

    @property
    def term_to_description(self) -> dict:
        return self._lookup_tables.term_to_description(list(self))

    @property
    def term_to_index(self) -> list:
        return self._lookup_tables.term_to_index(list(self))

    @property
    def index_to_term(self, indexes: list) -> list:
        return self._lookup_tables.index_to_term(indexes)

    @property
    def description_to_term(self, descriptions: list) -> list:
        return self._lookup_tables.description_to_term(descriptions)
