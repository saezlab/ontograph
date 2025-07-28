"""Registry for CSV adapters."""

import importlib
import pkgutil
import sys
from pathlib import Path
from typing import (
    List,
    Dict,
    Type,
    Optional,
)

# from .._core.ports import OntologyBackendPort
from ontograph._core.ports import OntologyBackendPort


# ---- Classes
class AdapterRegistry:
    """Registry for Backend adapters."""

    _adapters: Dict[str, Type[OntologyBackendPort]] = {}
    _default_adapter: Optional[str] = None

    @classmethod
    def register(
        cls, name: str, adapter_cls: Type[OntologyBackendPort], default: bool = False
    ) -> None:
        """
        Register a Backend adapter.

        Args:
            name: Name of the adapter
            adapter_cls: Adapter class
            default: Whether this adapter is the default one
        """
        cls._adapters[name] = adapter_cls
        if default:
            cls._default_adapter = name

    @classmethod
    def get(cls, name: Optional[str] = None) -> Type[OntologyBackendPort]:
        """
        Get an adapter by name.

        Args:
            name: Name of the adapter, or None to get the default adapter

        Returns:
            Adapter class

        Raises:
            ValueError: If the adapter is not found or no default adapter is set
        """
        if name is None:
            if cls._default_adapter is None:
                raise ValueError("No default adapter is set.")
            name = cls._default_adapter

        adapter_cls = cls._adapters.get(name)
        if adapter_cls is None:
            available = ", ".join(cls._adapters.keys())
            raise ValueError(
                f"Adapter '{name}' not found. Available adapters: {available}"
            )

        return adapter_cls

    @classmethod
    def list_adapters(cls) -> list[str]:
        """Return a list of registered adapter names."""
        return list(cls._adapters.keys())


# Functions to expose
def register_adapter(
    name: str, adapter_cls: Type[OntologyBackendPort], default: bool = False
) -> None:
    """Register an adapter."""
    AdapterRegistry.register(name, adapter_cls, default)


def get_adapter(name: Optional[str] = None) -> Type[OntologyBackendPort]:
    """Get an adapter by name."""
    return AdapterRegistry.get(name)


def discover_and_register_adapters(package_path: Optional[str] = None) -> List[str]:
    """
    Dynamically discover and register all available adapters in the package.

    Args:
        package_path: Dotted path to the package to scan, defaults to adapters directory

    Returns:
        List of names of successfully registered adapters
    """
    registered = []

    # Default to the backends package if none provided
    if package_path is None:
        package_path = "ontograph._adapters.backends"

    try:
        # Import the package itself
        package = importlib.import_module(package_path)

        # Get the physical directory of the package
        if hasattr(package, "__path__"):
            package_dir = package.__path__
        else:
            print(f"Package {package_path} has no __path__")
            return registered

        print(f"Scanning for adapters in {package_dir}")

        # Iterate through all modules in the package
        for _, module_name, is_pkg in pkgutil.iter_modules(package_dir):
            # Skip __init__ and other special modules
            if module_name.startswith("_"):
                continue

            # Skip sub-packages
            if is_pkg:
                continue

            print(f"Found module: {module_name}")

            # Attempt to import the module
            try:
                # Import the module with correct fully qualified name
                full_module_name = f"{package_path}.{module_name}"
                print(f"Importing: {full_module_name}")
                importlib.import_module(full_module_name)
                registered.append(module_name)
            except ImportError as e:
                # Log the error but continue with other adapters
                print(f"Could not load adapter {module_name}: {e}", file=sys.stderr)

    except ImportError as e:
        print(f"Could not import package {package_path}: {e}", file=sys.stderr)

    return registered
