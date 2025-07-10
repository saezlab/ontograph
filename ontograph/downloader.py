import os

from typing import Optional
import pooch

DEFAULT_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "downloader")


def download_file(
    url: str,
    fname: str,
    known_hash: Optional[str] = None,
    cache_dir: Optional[str] = None,
    show_progress: bool = True,
) -> str:
    """
    Download a file from a given URL and cache it locally.

    Parameters
    ----------
    url : str
        The full URL to download.
    known_hash : Optional[str], optional
        Expected file hash for validation (e.g., 'md5:<hash>'), by default None.
    cache_dir : Optional[str], optional
        Directory to cache the file, by default None which uses a default cache path.
    show_progress : bool, optional
        Show progress bar during download, by default True.

    Returns
    -------
    str
        The local file path of the cached download.
    """
    cache_path = cache_dir or DEFAULT_CACHE_DIR
    os.makedirs(cache_path, exist_ok=True)

    file_path = pooch.retrieve(
        url=url,
        known_hash=known_hash,
        fname=fname,
        path=cache_path,
        progressbar=show_progress,
    )
    return file_path
