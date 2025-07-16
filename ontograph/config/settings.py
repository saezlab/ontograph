from pathlib import Path

__all__ = [
    'DEFAULT_CACHE_DIR',
    'OBO_FOUNDRY_REGISTRY_URL',
    'SUPPORTED_FORMATS',
]

DEFAULT_CACHE_DIR = Path.home() / '.ontograph_cache'
OBO_FOUNDRY_REGISTRY_URL = 'http://obofoundry.org/registry/ontologies.yml'
SUPPORTED_FORMATS = ['obo', 'owl']
