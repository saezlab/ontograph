from pathlib import Path
from typing import Any, Optional, Type

from ontograph.ports.downloader import AbstractDownloader
from ontograph.ports.graph_backend import GraphBackend
from ontograph.ports.ontology_loader import OntologyLoaderPort
from ontograph.adapters.pooch_downloader import PoochDownloader
from ontograph.adapters.pronto_loader import ProntoOntologyLoader
from ontograph.adapters.pronto_graph import ProntoGraph


class OntographContainer:
    """Dependency injection container for Ontograph."""

    _downloader_cls: Type[AbstractDownloader] = PoochDownloader
    _loader_cls: Type[OntologyLoaderPort] = ProntoOntologyLoader
    _graph_cls: Type[GraphBackend] = ProntoGraph

    @classmethod
    def configure(
        cls,
        downloader_cls: Optional[Type[AbstractDownloader]] = None,
        loader_cls: Optional[Type[OntologyLoaderPort]] = None,
        graph_cls: Optional[Type[GraphBackend]] = None,
    ) -> None:
        """Configure the container with specific implementations."""
        if downloader_cls:
            cls._downloader_cls = downloader_cls
        if loader_cls:
            cls._loader_cls = loader_cls
        if graph_cls:
            cls._graph_cls = graph_cls

    @classmethod
    def get_downloader(cls, cache_dir: Optional[Path] = None) -> AbstractDownloader:
        """Get configured downloader implementation."""
        cache_dir = cache_dir or Path.home() / ".ontograph_cache"
        return cls._downloader_cls(cache_dir)

    @classmethod
    def get_loader(cls, cache_dir: Optional[Path] = None) -> OntologyLoaderPort:
        """Get configured ontology loader implementation."""
        cache_dir = cache_dir or Path.home() / ".ontograph_cache"
        return cls._loader_cls(cache_dir)

    @classmethod
    def get_graph_backend(cls, ontology: Any) -> GraphBackend:
        """Get configured graph backend implementation."""
        return cls._graph_cls(ontology)
