import logging
from pathlib import Path
from functools import cached_property

from ontograph._config import (
    DEFAULT_CACHE_DIR,
    SUPPORTED_FORMATS_ONTOGRAPH,
)
from ontograph._core.models import (
    Ontology,
    CatalogOntologies,
)
from ontograph._core.ports import OntologyBackendPort
from ontograph._utils.downloader import PoochDownloader
from ontograph._utils.registry import register_adapter

# Setup module logger
logger = logging.getLogger(__name__)

try:
    logger.debug(f"Secure import of Pronto library")
    import pronto

    PRONTO_AVAILABLE = True
    logger.debug(f"Pronto is available: {PRONTO_AVAILABLE}")
except ImportError:
    PRONTO_AVAILABLE = False


# ------------------------------------------------
# ----          Pronto Loader Adapter         ----
# ------------------------------------------------
class ProntoLoaderAdapter(OntologyBackendPort):
    """Adapter for loading ontologies using the Pronto library."""

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        """Initialize the adapter with a cache directory.

        Args:
            cache_dir: Directory to store downloaded ontologies.
        """
        logger.debug(f"Initializing ProntoLoaderAdapter with cache_dir: {cache_dir}")
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR

        # Create cache directory if this one doesn't exist.
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Using cache directory: {self.cache_dir}")

    @cached_property
    def catalog(self) -> CatalogOntologies:
        """Return the ontology catalog.

        Returns:
            The ontology catalog instance.
        """
        logger.debug("Initializing ontology catalog")
        return CatalogOntologies(cache_dir=self.cache_dir)

    def _extract_ontology_id(self, ontology_source: pronto.Ontology) -> str | None:
        """Extract ontology ID from metadata.

        Args:
            ontology_source: Loaded pronto ontology.

        Returns:
            Extracted ID or None if not found.
        """
        try:
            # Extract ontology ID from the pronto ontology if available
            ontology_id = ontology_source.metadata.ontology
            logger.debug(f"Raw ontology ID from metadata: {ontology_id}")

            # If ontology ID is an IRI, extract last part
            if isinstance(ontology_id, str) and (
                "/" in ontology_id or "." in ontology_id
            ):
                original_id = ontology_id

                # Extract the ID from the URL/IRI
                path = ontology_id
                ontology_id = path.split("/")[-1].split(".")[0]
                logger.debug(
                    f"Extracted ontology ID '{ontology_id}' from '{original_id}'"
                )

            return ontology_id
        except (AttributeError, KeyError, TypeError) as e:
            logger.info(f"Could not extract ontology ID from metadata: {str(e)}")
            return None

    def _load_ontology(self, file_path: Path) -> tuple[pronto.Ontology, str | None]:
        """Internal helper method to load an ontology file.

        Args:
            file_path: Path to ontology file.

        Returns:
            Tuple of (ontology_source, ontology_id).

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If parsing fails.
        """
        logger.debug(f"Loading ontology from file: {file_path}")

        if not file_path.exists():
            logger.error(f"Ontology file not found: {file_path}")
            raise FileNotFoundError(f"Ontology file not found: {file_path}")

        try:
            logger.info(f"Parsing ontology file with Pronto: {file_path}")
            ontology_source = pronto.Ontology(file_path)
        except (TypeError, ValueError) as e:
            logger.exception(f"Failed to load ontology from {file_path}: {str(e)}")
            raise ValueError(f"Failed to load ontology from {file_path}: {str(e)}")

        # Extract ontology ID
        ontology_id = self._extract_ontology_id(ontology_source)

        logger.info(f"Loaded ontology with ID: {ontology_id}")
        return ontology_source, ontology_id

    def _download_ontology(self, name_id: str, format: str) -> Path:
        """Download ontology from registry.

        Args:
            name_id: Ontology identifier.
            format: File format (e.g., "obo").

        Returns:
            Path to downloaded file.

        Raises:
            FileNotFoundError: If download fails.
            RuntimeError: For other errors.
        """
        try:
            logger.debug("Creating ontology downloader")
            ontology_downloader = PoochDownloader(
                cache_dir=self.cache_dir, catalog=self.catalog
            )

            logger.debug(f"Preparing to download {name_id}.{format}")
            resources = [{"name_id": name_id, "format": format}]

            logger.info(f"Downloading ontology: {name_id}.{format}")
            downloaded_paths = ontology_downloader.fetch_batch(resources=resources)
            file_path = downloaded_paths.get(name_id)

            logger.debug(f"Download result path: {file_path}")

            if not file_path or not file_path.exists():
                logger.error(f"Failed to download ontology: {name_id}.{format}")
                raise FileNotFoundError(
                    f"Failed to download ontology: {name_id}.{format}"
                )

            logger.info(f"Ontology downloaded successfully to {file_path}")
            return file_path
        except Exception as e:
            logger.exception(f"Error downloading ontology {name_id}: {str(e)}")
            raise RuntimeError(f"Error downloading ontology {name_id}: {str(e)}")

    def load_from_file(self, path_file: str) -> Ontology:
        """Load ontology from local file.

        Args:
            path_file: Path to ontology file.

        Returns:
            Loaded Ontology object.

        Raises:
            FileNotFoundError: If file not found.
            ValueError: If parsing fails.
        """
        logger.info(f"Loading ontology from file: {path_file}")
        path_file = Path(path_file)

        try:
            ontology_source, ontology_id = self._load_ontology(path_file)

            logger.debug(f"Creating Ontology object with ID: {ontology_id}")
            ontology = Ontology(
                ontology_source=ontology_source,
                ontology_id=ontology_id,
                metadata=ontology_source.metadata.annotations,
            )

            logger.info(f"Successfully loaded ontology from file: {path_file}")
            return ontology
        except (FileNotFoundError, ValueError) as e:
            logger.exception(f"Error loading ontology from file {path_file}: {str(e)}")
            raise

    def load_from_registry(self, name_id: str, format: str = "obo") -> Ontology:
        """Load ontology from registry, downloading if needed.

        Args:
            name_id: Ontology identifier.
            format: Ontology format (default: "obo").

        Returns:
            Loaded Ontology object.

        Raises:
            ValueError: If format is unsupported.
            FileNotFoundError: If file can't be found/downloaded.
            RuntimeError: For other errors.
        """
        logger.info(f"Loading ontology from registry: {name_id}.{format}")

        # Verify valid formats
        if format.lower() not in SUPPORTED_FORMATS_ONTOGRAPH:
            logger.error(f"Unsupported format requested: {format}")
            raise ValueError(f"Unsupported format: {format}")

        # Define path for the ontology based on name and format
        file_path = self.cache_dir.joinpath(f"{name_id}.{format}")

        logger.debug(f"Looking for ontology file at: {file_path}")

        # Download if needed
        if not file_path.exists():
            logger.info(
                f"Ontology file not found locally, downloading: {name_id}.{format}"
            )
            file_path = self._download_ontology(name_id, format)

        # Load the ontology
        try:
            logger.debug(f"Loading ontology from file: {file_path}")
            ontology_source, _ = self._load_ontology(file_path)

            # Get metadata from catalog
            logger.debug(f"Retrieving metadata for ontology: {name_id}")
            metadata = self.catalog.get_ontology_metadata(ontology_id=name_id)

            logger.debug(f"Creating Ontology object for {name_id}")
            ontology = Ontology(
                ontology_source=ontology_source,
                ontology_id=name_id,  # Use the requested ID from registry
                metadata=metadata,
            )

            logger.info(f"Successfully loaded ontology from registry: {name_id}")
            return ontology
        except Exception as e:
            logger.exception(f"Error creating Ontology object for {name_id}: {str(e)}")
            raise


# Self-registration (only if pandas is available)
if PRONTO_AVAILABLE:
    # Register this adapter with the registry
    register_adapter("pronto", ProntoLoaderAdapter, default=True)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    cache_dir = "./data/in/"

    adapter = ProntoLoaderAdapter(cache_dir=cache_dir)

    # Code for testing the load_from_file()
    path_test = "./data/in/go_version1.obo"
    print(f"Testing load_from_file with: {path_test}")
    onto_file = adapter.load_from_file(path_test)
    print(f"Loaded ontology: {onto_file._ontology_id}")
    print(f"Number of terms: {len(onto_file._ontology.terms())}")

    ontology_id = "go"  # Use a valid ontology ID
    format = "obo"

    # Code for testing the load_from_registry()
    print(f"Testing load_from_registry with: {ontology_id}.{format}")
    onto_catalog = adapter.load_from_registry(ontology_id, format)
    print(f"Loaded ontology: {ontology_id}.{format}")
    print(f"Number of terms: {len(onto_catalog._ontology.terms())}")

    # TODO: Ready for improvement
