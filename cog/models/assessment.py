"""Harm assessment model — the result of evaluating risk before execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(str, Enum):
    """Ordered risk levels from benign to catastrophic."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def score(self) -> float:
        """Numeric score in [0.0, 1.0] corresponding to this risk level."""
        return {
            RiskLevel.NONE: 0.0,
            RiskLevel.LOW: 0.25,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.75,
            RiskLevel.CRITICAL: 1.0,
        }[self]

    def __gt__(self, other: "RiskLevel") -> bool:
        levels = list(RiskLevel)
        return levels.index(self) > levels.index(other)

    def __ge__(self, other: "RiskLevel") -> bool:
        return self == other or self > other


class Verdict(str, Enum):
    """Execution verdict produced by the harm assessor."""

    PROCEED = "proceed"       # Safe to execute with no modification.
    CAUTION = "caution"       # Execute with additional logging or approval.
    BLOCK = "block"           # Refuse execution entirely.
    ESCALATE = "escalate"     # Hand off to a human or higher authority.


@dataclass
class HarmAssessment:
    """
    Records the outcome of harm evaluation for a given signal and context.

    Attributes:
        risk_level:       Overall assessed risk level.
        identified_risks: Human-readable descriptions of identified risks.
        mitigations:      Suggested actions to reduce risk.
        verdict:          Recommended execution decision.
        confidence:       Assessor confidence in [0.0, 1.0].
        notes:            Free-form explanatory notes.
    """

    risk_level: RiskLevel
    identified_risks: list[str] = field(default_factory=list)
    mitigations: list[str] = field(default_factory=list)
    verdict: Verdict = Verdict.PROCEED
    confidence: float = 1.0
    notes: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0.0, 1.0].")

    @property
    def is_safe(self) -> bool:
        """True when the verdict permits execution."""
        return self.verdict in (Verdict.PROCEED, Verdict.CAUTION)

    def __repr__(self) -> str:
        return (
            f"HarmAssessment(risk={self.risk_level.value}, "
            f"verdict={self.verdict.value}, confidence={self.confidence:.2f})"
        )
