from importlib.metadata import version
from pathlib import Path

from appdirs import user_cache_dir

__all__ = [
    'DEFAULT_CACHE_DIR',
    'NAME_OBO_FOUNDRY_CATALOG',
    'OBO_FOUNDRY_REGISTRY_URL',
    'PACKAGE_NAME',
    'PACKAGE_VERSION',
    'SUPPORTED_FORMATS_ONTOGRAPH',
    'DEFAULT_FORMAT_ONTOLOGY',
]

# Package metadata from installed package
PACKAGE_NAME = 'ontograph'
PACKAGE_VERSION = version(PACKAGE_NAME)

# Use package name (ontograph) from `pyproject.toml`` for cache directory
DEFAULT_CACHE_DIR = Path(
    user_cache_dir(appname=PACKAGE_NAME, version=PACKAGE_VERSION)
)

# Ontology catalog in OBO Foundry
NAME_OBO_FOUNDRY_CATALOG = 'obofoundry_registry.yml'
OBO_FOUNDRY_REGISTRY_URL = 'http://obofoundry.org/registry/ontologies.yml'


# List of supported formats in OntoGraph
SUPPORTED_FORMATS_ONTOGRAPH = ['obo', 'owl']
DEFAULT_FORMAT_ONTOLOGY = 'obo'

# TODO: Ready for improvement
