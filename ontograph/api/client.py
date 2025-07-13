from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ontograph.config.container import OntographContainer
from ontograph.core.ontology_graph import OntologyGraph
from ontograph.ports.downloader import AbstractDownloader
from ontograph.ports.ontology_loader import OntologyLoaderPort


class OntologyClient:
    """Facade for interacting with ontologies."""

    def __init__(self, cache_dir: Union[str, Path] = None):
        """
        Initialize the client.

        Args:
            cache_dir: Optional directory for caching ontology files
        """
        cache_dir = Path(cache_dir) if cache_dir else None
        self.loader: OntologyLoaderPort = OntographContainer.get_loader(cache_dir)
        self.downloader: AbstractDownloader = OntographContainer.get_downloader(cache_dir)
        self.ontology_graph = None

    def list_ontologies(self) -> List[Dict[str, str]]:
        """
        Get a list of all available ontologies from OBO Foundry.

        Returns:
            List[Dict[str, str]]: List of ontologies with their metadata
        """
        return self.downloader.list_available_ontologies()

    def get_ontology_formats(self, ontology_id: str) -> List[str]:
        """
        Get available formats for an ontology.

        Args:
            ontology_id: The ontology identifier

        Returns:
            List[str]: Available formats
        """
        return self.downloader.get_available_formats(ontology_id)

    def get_ontology_info(self, ontology_id: str) -> Optional[Dict]:
        """
        Get detailed metadata about an ontology.

        Args:
            ontology_id: The ontology identifier

        Returns:
            Optional[Dict]: Ontology metadata or None if not found
        """
        return self.downloader.get_ontology_metadata(ontology_id)

    def download(
        self, name_id: Union[str, List[Dict[str, str]]], format: str = "obo"
    ) -> Union[Path, Dict[str, Path]]:
        """
        Download ontology file(s).

        Args:
            name_id: Either a string identifier (e.g., 'go' for Gene Ontology)
                    or a list of dictionaries with 'name_id' and 'format' keys
            format: The file format ('obo' or 'owl'), used only when name_id is a string

        Returns:
            Union[Path, Dict[str, Path]]: Either a single path or a dictionary of paths
                                        mapping ontology IDs to their cached locations

        Examples:
            # List available ontologies
            client.list_ontologies()

            # Check available formats
            client.get_ontology_formats("go")

            # Get ontology metadata
            client.get_ontology_info("go")

            # Single download
            client.download("go", format="obo")

            # Batch download
            client.download([
                {"name_id": "go", "format": "obo"},
                {"name_id": "chebi", "format": "owl"}
            ])
        """
        if isinstance(name_id, str):
            # Single download
            url = self.downloader._get_download_url(name_id, format)
            if not url:
                raise ValueError(
                    f"Cannot find download URL for ontology {name_id} in format {format}"
                )
            return self.downloader.fetch(url, f"{name_id}.{format}")
        else:
            # Batch download
            return self.downloader.fetch_batch(name_id)

    def load(self, name_id: str, format: str = "obo") -> OntologyGraph:
        """
        Load an ontology and return an OntologyGraph instance.

        Args:
            name_id: The ontology identifier
            format: The file format

        Returns:
            OntologyGraph: The loaded ontology graph
        """
        pronto_ontology = self.loader.load(name_id, format)
        self.ontology_graph = OntologyGraph(pronto_ontology)
        return self.ontology_graph

    def load_batch(self, resources: List[Dict[str, str]]) -> Dict[str, OntologyGraph]:
        """
        Load multiple ontologies and return their graph instances.

        Args:
            resources: List of dictionaries with 'name_id' and optional 'format' keys

        Returns:
            Dict[str, OntologyGraph]: Dictionary mapping ontology IDs to their graph instances
        """
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
