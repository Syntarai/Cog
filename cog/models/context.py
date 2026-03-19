"""Context model — the restored situational awareness surrounding a decision."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from cog.models.signal import Signal


@dataclass
class Context:
    """
    Captures all situational information required for informed decision-making.

    COG restores context before acting, preventing decisions made without
    adequate understanding of history, environment, and constraints.

    Attributes:
        environment:  Deployment environment (e.g. "production", "staging").
        state:        Current system state snapshot (key-value).
        history:      Prior signals relevant to this decision.
        stakeholders: Identifiers of parties affected by the decision.
        constraints:  Active rules or policies constraining valid actions.
        id:           Auto-generated unique identifier.
        timestamp:    Creation time in UTC.
        metadata:     Optional key-value pairs for additional context.
    """

    environment: str
    state: dict[str, Any] = field(default_factory=dict)
    history: list[Any] = field(default_factory=list)
    stakeholders: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_history(self, signal: "Signal") -> None:
        """Append a signal to the context history."""
        self.history.append(signal)

    def add_constraint(self, constraint: str) -> None:
        """Register a new constraint."""
        if constraint not in self.constraints:
            self.constraints.append(constraint)

    def has_constraint(self, constraint: str) -> bool:
        """Check whether a specific constraint is active."""
        return constraint in self.constraints

    def __repr__(self) -> str:
        return (
            f"Context(id={self.id!r}, environment={self.environment!r}, "
            f"constraints={len(self.constraints)}, history={len(self.history)})"
        )
