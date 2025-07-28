"""Backend adapters package."""

from ontograph._utils.registry import discover_and_register_adapters

# Don't expose anything from this package - it's only used for registration
__all__ = []

# Automatically register all adapters when the package is imported
discover_and_register_adapters("ontograph._adapters.backends")
