# Basics: Downloading Ontologies

This minimal tutorial shows how to download ontologies using either Pooch or Download Manager, and how to load from the catalog or a URL.

---

## 1. Choose a Global Default Downloader

Set the default once in `ontograph/config/settings.py`:

```python
DEFAULT_DOWNLOADER = "pooch"
# or
DEFAULT_DOWNLOADER = "download_manager"
```

Now any client will use the configured backend unless you pass a downloader explicitly.
Only client classes accept backend strings; lower-level components expect a downloader adapter instance.

---

## 2. Use Pooch Explicitly

```python
from ontograph.client import ClientCatalog, ClientOntology
from ontograph.downloader import PoochDownloaderAdapter
from ontograph.config.settings import DEFAULT_CACHE_DIR

downloader = PoochDownloaderAdapter(cache_dir=DEFAULT_CACHE_DIR)

catalog = ClientCatalog(cache_dir="./data/out", downloader=downloader)
catalog.load_catalog()

client = ClientOntology(cache_dir="./data/out", downloader=downloader)
client.load(source="go")  # catalog download
```

---

## 3. Use Download Manager Explicitly

```python
from ontograph.client import ClientCatalog, ClientOntology
from ontograph.downloader import DownloadManagerAdapter
from ontograph.config.settings import DEFAULT_CACHE_DIR

downloader = DownloadManagerAdapter(
    cache_dir=DEFAULT_CACHE_DIR,
    backend="requests",
)

catalog = ClientCatalog(cache_dir="./data/out", downloader=downloader)
catalog.load_catalog()

client = ClientOntology(cache_dir="./data/out", downloader=downloader)
client.load(source="go")  # catalog download
```

---

## 4. Download From a URL

```python
from ontograph.client import ClientOntology
from ontograph.downloader import PoochDownloaderAdapter
from ontograph.config.settings import DEFAULT_CACHE_DIR

downloader = PoochDownloaderAdapter(cache_dir=DEFAULT_CACHE_DIR)

# URL to GO ontology
source_go = "https://purl.obolibrary.org/obo/go.obo"

client = ClientOntology(cache_dir=DEFAULT_CACHE_DIR, downloader=downloader)
client.load(source=source_go)
```
