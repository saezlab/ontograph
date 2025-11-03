"""Ontology loader module for OntoGraph.

This module provides abstract and concrete classes for loading ontologies
from files, catalogs, and URLs. It supports adapters for different ontology
formats and integrates with downloader and catalog utilities.
"""

from abc import ABC, abstractmethod
from typing import Any
import logging
from pathlib import Path
from functools import cached_property

import pronto
from charset_normalizer import from_path

from ontograph.models import Ontology, CatalogOntologies
from ontograph.downloader import (
    DownloaderPort,
    PoochDownloaderAdapter,
)
from ontograph.config.settings import (
    DEFAULT_CACHE_DIR,
    SUPPORTED_FORMATS_ONTOGRAPH,
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

__all__ = [
    'OntologyLoaderPort',
    'ProntoLoaderAdapter',
    'FastoboAdapter',
]


class OntologyLoaderPort(ABC):
    """Abstract base class for ontology loader ports.

    Defines the interface for loading ontologies from files, catalogs, and URLs.
    """

    @abstractmethod
    def load_from_file(self, file_path_ontology: str | Path) -> Ontology:
        """Load ontology from a file.

        Args:
            file_path_ontology (str | Path): Path to the ontology file.

        Returns:
            Ontology: Loaded ontology object.
        """
        pass

    @abstractmethod
    def load_from_catalog(self, name_id: str, format: str = 'obo') -> Ontology:
        """Load ontology from a catalog.

        Args:
            name_id (str): Ontology identifier.
            format (str, optional): Ontology format. Defaults to 'obo'.

        Returns:
            Ontology: Loaded ontology object.
        """
        pass

    @abstractmethod
    def load_from_url(
        self,
        url_ontology: str,
        filename: str,
        downloader: DownloaderPort | None = None,
    ) -> Ontology:
        """Load ontology from a URL.

        Args:
            url_ontology (str): URL to download the ontology from.
            filename (str): Name to save the downloaded file as.
            downloader (DownloaderPort | None, optional): Downloader implementation. Defaults to None.

        Returns:
            Ontology: Loaded ontology object.
        """
        pass


class ProntoLoaderAdapter(OntologyLoaderPort):
    """Concrete implementation of OntologyLoaderPort using Pronto.

    Loads ontologies from files, catalogs, and URLs using the Pronto library.
    """

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        """Initialize the ProntoLoaderAdapter.

        Args:
            cache_dir (str | Path | None, optional): Directory for cached files. Defaults to None.
        """
        self._cache_dir: Path | None = (
            Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        )
        self._ontology: Ontology | None = None

    @cached_property
    def catalog(self) -> CatalogOntologies:
        """Return the ontology catalog.

        Returns:
            CatalogOntologies: The ontology catalog instance.
        """
        logger.debug('Initializing ontology catalog')
        return CatalogOntologies(cache_dir=self._cache_dir)

    @property
    def cache_dir(self) -> Path:
        """Return the cache directory.

        Returns:
            Path: Path to the cache directory.

        Raises:
            ValueError: If cache_dir is not set.
        """
        if self._cache_dir is None:
            raise ValueError('Cache directory not set')
        return self._cache_dir

    def _extract_ontology_id(self, ontology: pronto.Ontology) -> str | None:
        """Extract ontology ID from metadata.

        Args:
            ontology (pronto.Ontology): Loaded pronto ontology.

        Returns:
            Optional[str]: Extracted ID or None if not found.
        """
        try:
            ontology_id: str | None = ontology.metadata.ontology
            logger.debug(f'Raw ontology ID from metadata: {ontology_id}')

            if isinstance(ontology_id, str) and (
                '/' in ontology_id or '.' in ontology_id
            ):
                original_id: str = ontology_id
                path: str = ontology_id
                ontology_id = path.split('/')[-1].split('.')[0]
                logger.debug(
                    f"Extracted ontology ID '{ontology_id}' from '{original_id}'"
                )

            return ontology_id
        except (AttributeError, KeyError, TypeError) as e:
            logger.exception(
                f'Could not extract ontology ID from metadata: {str(e)}'
            )
            return None

    def find_file_encoding(self, file):
        result = from_path(file).best()
        return result.encoding

    def _load_ontology(
        self, path_file: Path
    ) -> tuple[pronto.Ontology, str | None]:
        """Internal helper method to load an ontology file.

        Args:
            path_file (Path): Path to ontology file.

        Returns:
            tuple: (ontology, ontology_id).

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If parsing fails.
        """
        logger.debug(f'Loading ontology from file: {path_file}')
        if not path_file.exists():
            error_msg = f'Ontology file not found: {path_file}'
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        logger.debug(f'Parsing ontology file with Pronto: {path_file}')
        try:
            ontology: pronto.Ontology = pronto.Ontology(
                path_file, encoding=self.find_file_encoding(path_file)
            )
        except (TypeError, ValueError) as e:
            error_msg = f'Failed to load ontology from {path_file}: {str(e)}'
            logger.exception(error_msg)
            raise ValueError(error_msg) from e

        ontology_id: str | None = self._extract_ontology_id(ontology)
        logger.debug(f'Loaded ontology with ID: {ontology_id}')
        return ontology, ontology_id

    def _create_ontology_object(
        self,
        ontology_source: pronto.Ontology,
        ontology_id: str | None,
        metadata: dict[str, Any],
        source_description: str,
    ) -> Ontology:
        """Create an Ontology object with logging.

        Args:
            ontology_source (pronto.Ontology): The source ontology object.
            ontology_id (str | None): ID for the ontology.
            metadata (dict[str, Any]): Metadata for the ontology.
            source_description (str): Description of source for logging purposes.

        Returns:
            Ontology: The created ontology object.

        Raises:
            Exception: If ontology creation fails.
        """
        try:
            logger.debug(f'Creating Ontology object with ID: {ontology_id}')
            ontology = Ontology(
                ontology_source=ontology_source,
                ontology_id=ontology_id,
                metadata=metadata,
            )
            logger.debug(
                f'Successfully loaded ontology from {source_description}'
            )
            return ontology
        except Exception as e:
            error_msg = (
                f'Error creating Ontology object for {ontology_id}: {str(e)}'
            )
            logger.exception(error_msg)
            raise Exception(error_msg) from e

    def load_from_file(self, file_path_ontology: str | Path) -> Ontology:
        """Load ontology from a file.

        Args:
            file_path_ontology (str | Path): Path to the ontology file.

        Returns:
            Ontology: Loaded Ontology object.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If parsing fails.
        """
        file_path = Path(file_path_ontology)
        try:
            ontology_object, ontology_id = self._load_ontology(file_path)
            return self._create_ontology_object(
                ontology_source=ontology_object,
                ontology_id=ontology_id,
                metadata=ontology_object.metadata.annotations,
                source_description=f'file: {file_path}',
            )
        except (FileNotFoundError, ValueError) as e:
            logger.exception(
                f'Error loading ontology from file {file_path}: {str(e)}'
            )
            raise

    def _download_ontology(self, name_id: str, format: str) -> Path:
        """Download ontology from catalog.

        Args:
            name_id (str): Ontology identifier.
            format (str): Ontology format.

        Returns:
            Path: Path to downloaded file.

        Raises:
            FileNotFoundError: If file can't be downloaded.
            NotImplementedError: If download functionality is not implemented.
        """
        downloader = PoochDownloaderAdapter(cache_dir=self.cache_dir)
        logger.debug(f'Created default downloader: {type(downloader).__name__}')

        resources = [{'name_id': name_id, 'format': format}]
        try:
            path_download = downloader.fetch_from_catalog(
                resources=resources, catalog=self.catalog
            )
        except NotImplementedError as err:
            logger.error(f'Download functionality not implemented: {err}')
            raise NotImplementedError(
                f'Download functionality not implemented: {err}'
            ) from err
        except Exception as err:
            logger.exception(
                f'Error downloading ontology {name_id} in format {format}: {err}'
            )
            raise RuntimeError(
                f'Failed to download ontology {name_id} in format {format}: {err}'
            ) from err

        return path_download[name_id]

    def load_from_catalog(self, name_id: str, format: str = 'obo') -> Ontology:
        """Load ontology from the OBO Foundry catalog, downloading if needed.

        Args:
            name_id (str): Ontology identifier.
            format (str, optional): Ontology format. Defaults to "obo".

        Returns:
            Ontology: Loaded Ontology object.

        Raises:
            ValueError: If format is unsupported.
            FileNotFoundError: If file can't be found/downloaded.
            RuntimeError: For other errors.
        """
        logger.debug(f'Loading ontology from catalog: {name_id}.{format}')

        if format.lower() not in SUPPORTED_FORMATS_ONTOGRAPH:
            logger.error(f'Unsupported format requested: {format}')
            raise ValueError(f'Unsupported format: {format}')

        file_path: Path = self.cache_dir.joinpath(f'{name_id}.{format}')
        logger.debug(f'Looking for ontology file at: {file_path}')

        if not file_path.exists():
            logger.debug(
                f'Ontology file not found locally, downloading: {name_id}.{format}'
            )
            file_path = self._download_ontology(name_id, format)

        logger.debug(f'Loading ontology from file: {file_path}')
        ontology_source, _ = self._load_ontology(file_path)

        logger.debug(f'Retrieving metadata for ontology: {name_id}')
        metadata: dict[str, Any] = self.catalog.get_ontology_metadata(
            ontology_id=name_id
        )

        return self._create_ontology_object(
            ontology_source=ontology_source,
            ontology_id=name_id,
            metadata=metadata,
            source_description=f'registry: {name_id}',
        )

    def load_from_url(
        self,
        url_ontology: str,
        filename: str,
        downloader: DownloaderPort | None = None,
    ) -> Ontology:
        """Load ontology from URL.

        Args:
            url_ontology (str): URL to download from.
            filename (str): Name to save the file as.
            downloader (DownloaderPort | None, optional): Downloader implementation. Defaults to None.

        Returns:
            Ontology: Loaded Ontology object.

        Raises:
            FileNotFoundError: If file can't be downloaded.
            ValueError: If parsing fails.
        """
        if downloader is None:
            downloader = PoochDownloaderAdapter(cache_dir=self.cache_dir)
            logger.debug(
                f'Created default downloader: {type(downloader).__name__}'
            )

        file_path: Path = downloader.fetch_from_url(
            url_ontology=url_ontology,
            filename=filename,
        )
        logger.debug(f'Downloaded ontology to: {file_path}')

        ontology_source, ontology_id = self._load_ontology(file_path)

        return self._create_ontology_object(
            ontology_source=ontology_source,
            ontology_id=ontology_id,
            metadata=ontology_source.metadata.annotations,
            source_description=f'URL: {url_ontology}',
        )


class FastoboAdapter(OntologyLoaderPort):
    """Concrete implementation of OntologyLoaderPort for Fastobo format.

    (Not yet implemented.)
    """

    pass
