"""Configuration constants and settings for the ontograph package."""

from pathlib import Path


class RegistryConfig:
    """Configuration for OBO Foundry registry."""

    # Base URLs
    OBO_FOUNDRY_BASE = "http://obofoundry.org"

    # Registry URLs in different formats
    REGISTRY = {
        "yaml": f"{OBO_FOUNDRY_BASE}/registry/ontologies.yml",
        "jsonld": f"{OBO_FOUNDRY_BASE}/registry/registry.jsonld",
        "ttl": f"{OBO_FOUNDRY_BASE}/registry/registry.ttl",
    }

    # Default format
    DEFAULT_FORMAT = "yaml"

    @classmethod
    def get_registry_url(cls, format: str = None) -> str:
        """
        Get the registry URL for a specific format.

        Args:
            format: The desired format (yaml, jsonld, or ttl)
                   If None, returns URL for default format

        Returns:
            str: The registry URL

        Raises:
            ValueError: If the format is not supported
        """
        format = format or cls.DEFAULT_FORMAT
        if format not in cls.REGISTRY:
            raise ValueError(
                f"Unsupported format: {format}. "
                f"Use one of: {list(cls.REGISTRY.keys())}"
            )
        return cls.REGISTRY[format]


class CacheConfig:
    """Configuration for caching."""

    # Default cache location
    DEFAULT_CACHE_DIR = Path.home() / ".ontograph_cache"

    # Cache file names
    REGISTRY_CACHE = "obofoundry_registry.yml"

    @classmethod
    def get_cache_dir(cls) -> Path:
        """Get the default cache directory."""
        return cls.DEFAULT_CACHE_DIR


class OntologyFormats:
    """Supported ontology formats."""

    OBO = "obo"
    OWL = "owl"

    # List of all supported formats
    SUPPORTED = [OBO, OWL]

    # Default format
    DEFAULT = OBO
