from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ontograph.core.ontology_graph import OntologyGraph
from ontograph.ports.downloader_port import DownloaderPort
from ontograph.ports.ontology_loader_port import OntologyLoaderPort


class OntologyClient:
    """Facade for interacting with ontologies."""

    def __init__(self, downloader: DownloaderPort, loader: OntologyLoaderPort):
        """
        Initialize the client.

        Args:
            downloader: The downloader port to use for fetching ontologies
            loader: The loader port to use for loading ontologies
        """
        self.downloader = downloader
        self.loader = loader
        self.ontology_graph = None

    def list_ontologies(self) -> List[Dict[str, str]]:
        """Get a list of all available ontologies from OBO Foundry."""
        return self.downloader.list_available_ontologies()

    def get_ontology_formats(self, ontology_id: str) -> List[str]:
        """Get available formats for an ontology."""
        return self.downloader.get_available_formats(ontology_id)

    def get_ontology_info(self, ontology_id: str) -> Optional[Dict]:
        """Get detailed metadata about an ontology."""
        return self.downloader.get_ontology_metadata(ontology_id)

    def download(
        self, name_id: Union[str, List[Dict[str, str]]], format: str = "obo"
    ) -> Union[Path, Dict[str, Path]]:
        """Download ontology file(s)."""
        if isinstance(name_id, str):
            url = self.downloader.get_download_url(name_id, format)
            if not url:
                raise ValueError(
                    f"Cannot find download URL for ontology {name_id} in format {format}"
                )
            return self.downloader.fetch(url, f"{name_id}.{format}")
        else:
            return self.downloader.fetch_batch(name_id)

    def load(self, name_id: str, format: str = "obo") -> OntologyGraph:
        """Load an ontology and return an OntologyGraph instance."""
        pronto_ontology = self.loader.load(name_id, format)
        self.ontology_graph = OntologyGraph(pronto_ontology)
        return self.ontology_graph

    def load_batch(self, resources: List[Dict[str, str]]) -> Dict[str, OntologyGraph]:
        """Load multiple ontologies and return their graph instances."""
        graphs = {}
        for resource in resources:
            name_id = resource["name_id"]
            format = resource.get("format", "obo")
            graphs[name_id] = self.load(name_id, format)
        return graphs

    def get_term(self, term_id: str) -> Optional[Any]:
        """Get details for a specific term."""
        if not self.ontology_graph:
            raise RuntimeError("No ontology loaded. Call load() first.")
        return self.ontology_graph.get_term(term_id)

    def get_parents(self, term_id: str) -> List[str]:
        """Get immediate parent terms."""
        if not self.ontology_graph:
            raise RuntimeError("No ontology loaded. Call load() first.")
        return self.ontology_graph.get_parents(term_id)

    def get_children(self, term_id: str) -> List[str]:
        """Get immediate child terms."""
        if not self.ontology_graph:
            raise RuntimeError("No ontology loaded. Call load() first.")
        return self.ontology_graph.get_children(term_id)

    def get_ancestors(self, term_id: str) -> List[str]:
        """Get all ancestor terms."""
        if not self.ontology_graph:
            raise RuntimeError("No ontology loaded. Call load() first.")
        return self.ontology_graph.get_ancestors(term_id)

    def get_descendants(self, term_id: str) -> List[str]:
        """Get all descendant terms."""
        if not self.ontology_graph:
            raise RuntimeError("No ontology loaded. Call load() first.")
        return self.ontology_graph.get_descendants(term_id)

    def query(self, expression: str) -> List[str]:
        """Execute a query against the ontology."""
        if not self.ontology_graph:
            raise RuntimeError("No ontology loaded. Call load() first.")
        return self.ontology_graph.query(expression)

    def metadata(self) -> Dict[str, Any]:
        """Get ontology metadata."""
        if not self.ontology_graph:
            raise RuntimeError("No ontology loaded. Call load() first.")
        return self.ontology_graph.metadata()
