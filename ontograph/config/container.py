"""
Dependency Injection Container for Ontograph.
This module provides a centralized container for managing dependencies and implementations.
"""

from pathlib import Path
from typing import Any, Optional, Type

from ontograph.api.client import OntologyClient
from ontograph.config.settings import Settings
from ontograph.core.registry import OBOFoundryRegistry
from ontograph.ports.downloader_port import DownloaderPort
from ontograph.ports.graph_backend_port import GraphBackend
from ontograph.ports.ontology_loader_port import OntologyLoaderPort
from ontograph.adapters.pooch_downloader_adapter import PoochDownloaderAdapter
from ontograph.adapters.pronto_loader import ProntoLoaderAdapter
from ontograph.adapters.pronto_graph import ProntoGraph


class OntographContainer:
    """
    Dependency injection container for Ontograph.

    This container manages the creation and configuration of all dependencies
    used throughout the application, following the hexagonal architecture pattern.

    Default implementations:
    - Downloader: PoochDownloader for downloading ontologies
    - Loader: ProntoOntologyLoader for loading ontology files
    - Graph Backend: ProntoGraph for graph operations
    """

    # Default implementation classes
    _downloader_cls: Type[DownloaderPort] = PoochDownloaderAdapter
    _loader_cls: Type[OntologyLoaderPort] = ProntoLoaderAdapter
    _graph_cls: Type[GraphBackend] = ProntoGraph

    @classmethod
    def configure(
        cls,
        downloader_cls: Optional[Type[DownloaderPort]] = None,
        loader_cls: Optional[Type[OntologyLoaderPort]] = None,
        graph_cls: Optional[Type[GraphBackend]] = None,
    ) -> None:
        """
        Configure the container with specific implementations.

        Args:
            downloader_cls: Implementation class for the downloader port
            loader_cls: Implementation class for the ontology loader port
            graph_cls: Implementation class for the graph backend port
        """
        if downloader_cls:
            cls._downloader_cls = downloader_cls
        if loader_cls:
            cls._loader_cls = loader_cls
        if graph_cls:
            cls._graph_cls = graph_cls

    @classmethod
    def get_downloader(cls, cache_dir: Optional[Path] = None) -> DownloaderPort:
        """
        Get configured downloader implementation.

        Args:
            cache_dir: Optional custom cache directory path

        Returns:
            Configured downloader instance
        """
        cache_dir = cache_dir or Settings.DEFAULT_CACHE_DIR
        registry = OBOFoundryRegistry(cache_dir)
        return cls._downloader_cls(cache_dir, registry)

    @classmethod
    def get_loader(cls, cache_dir: Optional[Path] = None) -> OntologyLoaderPort:
        """
        Get configured ontology loader implementation.

        Args:
            cache_dir: Optional custom cache directory path

        Returns:
            Configured ontology loader instance
        """
        cache_dir = cache_dir or Settings.DEFAULT_CACHE_DIR
        return cls._loader_cls(cache_dir)

    @classmethod
    def get_graph_backend(cls, ontology: Any) -> GraphBackend:
        """
        Get configured graph backend implementation.

        Args:
            ontology: Ontology object to be wrapped by the graph backend

        Returns:
            Configured graph backend instance
        """
        return cls._graph_cls(ontology)

    @classmethod
    def get_client(cls, cache_dir: Optional[Path] = None) -> OntologyClient:
        """
        Get fully configured client instance with all dependencies.

        This is the main entry point for using the library.

        Args:
            cache_dir: Optional custom cache directory path

        Returns:
            Configured OntologyClient instance
        """
        cache_dir = cache_dir or Settings.DEFAULT_CACHE_DIR
        downloader = cls.get_downloader(cache_dir)
        loader = cls.get_loader(cache_dir)
        return OntologyClient(
            downloader=downloader,
            loader=loader,
            graph_backend_factory=cls.get_graph_backend,
        )
