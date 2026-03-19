"""Decision model — the auditable output of a complete COG governance cycle."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from cog.models.signal import Signal
from cog.models.context import Context
from cog.models.assessment import HarmAssessment, Verdict


@dataclass
class ReasoningStep:
    """A single step in the chain of reasoning produced by the COG engine.

    Attributes:
        index:       Position in the chain (0-indexed).
        description: Human-readable explanation of this reasoning step.
        inputs:      Values consumed at this step.
        output:      Value produced at this step.
        confidence:  Step-level confidence in [0.0, 1.0].
    """

    index: int
    description: str
    inputs: dict[str, Any] = field(default_factory=dict)
    output: Any = None
    confidence: float = 1.0

    def __repr__(self) -> str:
        return f"ReasoningStep({self.index}: {self.description!r})"


@dataclass
class ReasoningChain:
    """
    An ordered, auditable chain of reasoning steps leading to a decision.

    Exposes *why* the COG reached its conclusion — a core COG principle.

    Attributes:
        steps:      Ordered list of reasoning steps.
        conclusion: Plain-language summary of the chain's outcome.
        confidence: Overall chain confidence in [0.0, 1.0].
    """

    steps: list[ReasoningStep] = field(default_factory=list)
    conclusion: str = ""
    confidence: float = 1.0

    def add_step(
        self,
        description: str,
        inputs: dict[str, Any] | None = None,
        output: Any = None,
        confidence: float = 1.0,
    ) -> ReasoningStep:
        """Append a new step and return it."""
        step = ReasoningStep(
            index=len(self.steps),
            description=description,
            inputs=inputs or {},
            output=output,
            confidence=confidence,
        )
        self.steps.append(step)
        return step

    def __repr__(self) -> str:
        return (
            f"ReasoningChain(steps={len(self.steps)}, "
            f"confidence={self.confidence:.2f}, conclusion={self.conclusion!r})"
        )


@dataclass
class Decision:
    """
    The final, auditable outcome of a COG governance cycle.

    Each Decision records the full provenance of a governance event:
    the originating signal, restored context, reasoning chain, harm
    assessment, and the resulting verdict.

    Attributes:
        signal:     The signal that triggered this governance cycle.
        context:    The restored context used for evaluation.
        reasoning:  The chain of reasoning leading to the verdict.
        assessment: The harm assessment.
        verdict:    The final execution verdict.
        action:     The approved action payload (if any).
        id:         Auto-generated unique identifier.
        timestamp:  Timestamp of decision in UTC.
        cog_name:   Name of the COG that produced this decision.
    """

    signal: Signal
    context: Context
    reasoning: ReasoningChain
    assessment: HarmAssessment
    verdict: Verdict
    action: Any = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    cog_name: str = "default"

    @property
    def approved(self) -> bool:
        """True when the decision permits execution."""
        return self.verdict in (Verdict.PROCEED, Verdict.CAUTION)

    def summary(self) -> str:
        """Return a concise human-readable summary of this decision."""
        lines = [
            f"Decision {self.id}",
            f"  COG:      {self.cog_name}",
            f"  Signal:   [{self.signal.type}] from {self.signal.source}",
            f"  Context:  {self.context.environment} "
            f"({len(self.context.constraints)} constraints)",
            f"  Risk:     {self.assessment.risk_level.value} "
            f"(confidence {self.assessment.confidence:.0%})",
            f"  Verdict:  {self.verdict.value.upper()}",
            f"  Reasoning ({len(self.reasoning.steps)} steps): "
            f"{self.reasoning.conclusion}",
        ]
        if self.assessment.identified_risks:
            lines.append(
                f"  Risks:    {', '.join(self.assessment.identified_risks)}"
            )
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"Decision(id={self.id!r}, verdict={self.verdict.value}, "
            f"cog={self.cog_name!r})"
        )
