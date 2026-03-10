# ClientCatalog

`ClientCatalog` is the main interface for interacting with the ontology catalog in OntoGraph.  
It allows you to load the catalog, list available ontologies, retrieve metadata, and access download URLs and formats.

This class is ideal for users who want to explore the catalog of available ontologies, inspect their metadata, and prepare for ontology loading and analysis.

---

## Features

- Load and cache the ontology catalog from [OBO Foundry](https://obofoundry.org/)
- List all available ontologies and their metadata
- Retrieve metadata for a specific ontology
- Get download URLs and available formats for each ontology
- Print the catalog schema tree for exploration

## Usage

```python
from ontograph.client import ClientCatalog
from ontograph.downloader import DownloadManagerAdapter
from ontograph.config.settings import DEFAULT_CACHE_DIR

client_catalog = ClientCatalog(cache_dir="./data/out")

# Optional: use Download Manager for all catalog downloads
# downloader = DownloadManagerAdapter(cache_dir=DEFAULT_CACHE_DIR, backend="requests")
# client_catalog = ClientCatalog(cache_dir="./data/out", downloader=downloader)
```

---

## API Reference

::: ontograph.client.ClientCatalog

---

## See Also

- [ClientOntology](client-ontology.md): For loading and querying individual ontologies.
