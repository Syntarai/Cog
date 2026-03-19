"""ContextManager — restores situational context before a decision is made."""

from __future__ import annotations

from typing import Any, Callable

from cog.models.signal import Signal
from cog.models.context import Context
from cog.exceptions import ContextRestorationError


class ContextManager:
    """
    Responsible for restoring or constructing the Context for a given Signal.

    COG's first principle is: *restore context before action*. This component
    queries available state stores, history logs, and policy repositories to
    build a complete situational picture before the engine proceeds.

    Usage::

        manager = ContextManager(environment="production")
        manager.add_state_provider(lambda sig: {"user_tier": "admin"})
        manager.add_constraint_provider(lambda sig: ["no-delete-in-prod"])

        context = manager.restore(signal)

    Parameters:
        environment:       Target environment label.
        default_state:     Static baseline state always included.
        default_constraints: Static constraints always enforced.
        history_limit:     Maximum number of historical signals retained.
    """

    def __init__(
        self,
        environment: str = "default",
        default_state: dict[str, Any] | None = None,
        default_constraints: list[str] | None = None,
        history_limit: int = 100,
    ) -> None:
        self.environment = environment
        self.default_state: dict[str, Any] = default_state or {}
        self.default_constraints: list[str] = default_constraints or []
        self.history_limit = history_limit

        self._history: list[Signal] = []
        self._state_providers: list[Callable[[Signal], dict[str, Any]]] = []
        self._constraint_providers: list[Callable[[Signal], list[str]]] = []
        self._stakeholder_providers: list[Callable[[Signal], list[str]]] = []

    # ------------------------------------------------------------------
    # Provider registration
    # ------------------------------------------------------------------

    def add_state_provider(self, provider: Callable[[Signal], dict[str, Any]]) -> None:
        """Register a callable that contributes dynamic state for a signal."""
        self._state_providers.append(provider)

    def add_constraint_provider(
        self, provider: Callable[[Signal], list[str]]
    ) -> None:
        """Register a callable that contributes dynamic constraints for a signal."""
        self._constraint_providers.append(provider)

    def add_stakeholder_provider(
        self, provider: Callable[[Signal], list[str]]
    ) -> None:
        """Register a callable that identifies stakeholders for a signal."""
        self._stakeholder_providers.append(provider)

    # ------------------------------------------------------------------
    # Core operation
    # ------------------------------------------------------------------

    def restore(self, signal: Signal) -> Context:
        """
        Build and return the Context for *signal*.

        Merges static defaults with all registered provider outputs.

        Raises:
            ContextRestorationError: if any provider raises an exception.
        """
        state = dict(self.default_state)
        constraints = list(self.default_constraints)
        stakeholders: list[str] = []

        try:
            for provider in self._state_providers:
                state.update(provider(signal))

            for provider in self._constraint_providers:
                for c in provider(signal):
                    if c not in constraints:
                        constraints.append(c)

            for provider in self._stakeholder_providers:
                for s in provider(signal):
                    if s not in stakeholders:
                        stakeholders.append(s)
        except Exception as exc:
            raise ContextRestorationError(
                f"Context restoration failed for signal {signal.id!r}: {exc}"
            ) from exc

        recent_history = list(self._history[-self.history_limit :])

        context = Context(
            environment=self.environment,
            state=state,
            history=recent_history,
            stakeholders=stakeholders,
            constraints=constraints,
        )

        self._history.append(signal)
        return context

    def clear_history(self) -> None:
        """Flush the stored signal history."""
        self._history.clear()
