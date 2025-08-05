from pathlib import Path

import toml
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

# Read package information from pyproject.toml
_PYPROJECT_PATH = Path(__file__).parents[2] / 'pyproject.toml'
with open(_PYPROJECT_PATH, 'r') as f:
    _PYPROJECT = toml.load(f)

# Extract package metadata
PACKAGE_NAME = _PYPROJECT['project']['name']
PACKAGE_VERSION = _PYPROJECT['project']['version']

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
