"""CogRegistry — a named store of CogEngine instances within a verse."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cog.exceptions import CogNotFoundError

if TYPE_CHECKING:
    from cog.core.engine import CogEngine


class CogRegistry:
    """
    Stores and retrieves named CogEngine instances.

    Each entry in the registry represents a distinct decision-governance unit
    (a "cog") within the verse. Cogs are registered by name and retrieved
    on demand for signal processing or pipeline composition.

    Usage::

        registry = CogRegistry()
        registry.register("finance", finance_cog)
        cog = registry.get("finance")
    """

    def __init__(self) -> None:
        self._store: dict[str, "CogEngine"] = {}

    def register(self, name: str, cog: "CogEngine") -> None:
        """
        Add a CogEngine to the registry under *name*.

        Parameters:
            name: Unique identifier for this cog.
            cog:  The CogEngine instance to register.
        """
        self._store[name] = cog

    def unregister(self, name: str) -> None:
        """Remove a cog from the registry. No-op if not found."""
        self._store.pop(name, None)

    def get(self, name: str) -> "CogEngine":
        """
        Retrieve a registered CogEngine by name.

        Raises:
            CogNotFoundError: if *name* is not registered.
        """
        if name not in self._store:
            raise CogNotFoundError(name)
        return self._store[name]

    def has(self, name: str) -> bool:
        """Return True if *name* is registered."""
        return name in self._store

    def names(self) -> list[str]:
        """Return all registered cog names."""
        return list(self._store.keys())

    def __len__(self) -> int:
        return len(self._store)

    def __repr__(self) -> str:
        return f"CogRegistry(cogs={self.names()})"
