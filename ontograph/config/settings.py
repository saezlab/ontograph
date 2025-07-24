from pathlib import Path

import toml
from appdirs import user_cache_dir

__all__ = [
    'DEFAULT_CACHE_DIR',
    'OBO_FOUNDRY_REGISTRY_URL',
    'SUPPORTED_FORMATS',
    'PACKAGE_NAME',
    'PACKAGE_VERSION',
]

print(Path(__file__))

# Read package information from pyproject.toml
_PYPROJECT_PATH = Path(__file__).parents[2] / 'pyproject.toml'
with open(_PYPROJECT_PATH, 'r') as f:
    print(_PYPROJECT_PATH)
    _PYPROJECT = toml.load(f)

# Extract package metadata
PACKAGE_NAME = _PYPROJECT['project']['name']
PACKAGE_VERSION = _PYPROJECT['project']['version']

# Use package name from pyproject.toml for cache dir
DEFAULT_CACHE_DIR = Path(
    user_cache_dir(appname=PACKAGE_NAME, version=PACKAGE_VERSION)
)

# Ontology catalog in OBO Foundry
OBO_FOUNDRY_REGISTRY_URL = 'http://obofoundry.org/registry/ontologies.yml'

# List of supported formats in OntoGraph
SUPPORTED_FORMATS = ['obo', 'owl']
