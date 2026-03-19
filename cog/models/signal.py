"""Signal model — an incoming request or event entering the COG system."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Signal:
    """
    Represents an incoming signal (action request, command, or event)
    that the COG system must govern before execution.

    Attributes:
        type:     Category of signal (e.g. "action", "query", "command").
        payload:  The raw content or parameters of the signal.
        source:   Identifier of the originating agent, user, or system.
        id:       Auto-generated unique identifier.
        timestamp: Creation time in UTC.
        metadata: Optional key-value pairs for additional context.
        priority: Urgency level ("low", "normal", "high", "critical").
    """

    type: str
    payload: Any
    source: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"

    def __post_init__(self) -> None:
        valid_priorities = {"low", "normal", "high", "critical"}
        if self.priority not in valid_priorities:
            raise ValueError(
                f"Invalid priority '{self.priority}'. Must be one of {valid_priorities}."
            )

    def __repr__(self) -> str:
        return (
            f"Signal(id={self.id!r}, type={self.type!r}, "
            f"source={self.source!r}, priority={self.priority!r})"
        )
