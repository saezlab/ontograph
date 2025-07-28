"""Adapters package."""

# Import backends subpackage to trigger adapter registration
from . import backends

# Don't expose anything specific from this package
__all__ = []
