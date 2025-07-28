# Import core functionality
from ._client.client import load, catalog, get_available_backends

# Explicitly import adapters to ensure they're registered
import ontograph._adapters

# This explicit import ensures the pronto adapter is loaded
# You can remove this once the dynamic discovery is working
# import ontograph._adapters.backends.pronto_backend

__all__ = ["load", "catalog", "get_available_backends"]
