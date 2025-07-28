from pathlib import Path

from pooch import retrieve

from ontograph._core.models import CatalogOntologies

__all__ = [
    "PoochDownloader",
]


# ------------------------------------------------
# ----             Pooch Downloader           ----
# ------------------------------------------------
class PoochDownloader:
    def __init__(self, cache_dir: Path, catalog: CatalogOntologies) -> None:

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.catalog = catalog

    def _get_download_url(self, name_id: str, format: str) -> str | None:
        return self.catalog.get_download_url(name_id, format)

    def fetch(self, url: str, filename: str) -> Path:

        local_file = retrieve(
            url=url,
            known_hash=None,  # Could later integrate SHA256 checksums
            fname=filename,
            path=self.cache_dir,
            progressbar=True,
        )
        return Path(local_file)

    def fetch_batch(self, resources: list[dict[str, str]]) -> dict[str, Path]:

        if not resources:
            raise ValueError("Resources list for batch download is empty.")

        results = {}

        for resource in resources:
            name_id = resource.get("name_id")
            format = resource.get("format", "obo")  # Default to OBO format

            if not name_id:
                raise KeyError("Resource dictionary must contain 'name_id' key")

            # Get URL from registry
            url = self._get_download_url(name_id, format)
            if not url:
                raise ValueError(
                    f"Cannot find download URL for ontology {name_id} "
                    f"in format {format}"
                )

            filename = f"{name_id}.{format}"
            local_path = self.fetch(url, filename)
            results[name_id] = local_path

        return results


# -------------------------------------------------
# ----             Downloader Manager          ----
# -------------------------------------------------
class DownloadManager:
    pass
