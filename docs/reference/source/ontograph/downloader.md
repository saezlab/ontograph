# downloader

This module provides interfaces and adapters for downloading ontology files from URLs and catalogs.

## Default Downloader

OntoGraph selects a default downloader backend via `DEFAULT_DOWNLOADER` in
`ontograph/config/settings.py`. You can also override this per client by
passing a downloader adapter.

```python
from ontograph.downloader import get_default_downloader
from ontograph.config.settings import DEFAULT_CACHE_DIR

downloader = get_default_downloader(cache_dir=DEFAULT_CACHE_DIR)
```

---

## API Reference

::: ontograph.downloader

---
