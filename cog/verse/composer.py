"""CogComposer — builds multi-stage governance pipelines from named cogs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cog.models.signal import Signal
from cog.models.decision import Decision
from cog.models.assessment import Verdict
from cog.exceptions import PipelineError

if TYPE_CHECKING:
    from cog.core.engine import CogEngine
    from cog.verse.registry import CogRegistry


class CogPipeline:
    """
    An ordered sequence of CogEngines that process a Signal in series.

    Each stage receives the signal from the previous stage. If any stage
    blocks or escalates execution, the pipeline stops and returns that
    decision immediately — ensuring the strictest governance wins.

    Attributes:
        name:  Human-readable pipeline identifier.
        cogs:  Ordered list of CogEngine instances forming the pipeline.
    """

    def __init__(self, name: str, cogs: list["CogEngine"]) -> None:
        self.name = name
        self.cogs = cogs

    def run(self, signal: Signal) -> Decision:
        """
        Process *signal* through each stage in order.

        Stops early if any stage produces a BLOCK or ESCALATE verdict.

        Returns:
            Decision from the last stage that processed the signal.

        Raises:
            PipelineError: if no cogs are registered in this pipeline.
        """
        if not self.cogs:
            raise PipelineError(f"Pipeline '{self.name}' has no registered cogs.")

        last_decision: Decision | None = None

        for cog in self.cogs:
            decision = cog.process(signal)
            last_decision = decision

            # A blocking or escalating verdict ends the pipeline early
            if decision.verdict in (Verdict.BLOCK, Verdict.ESCALATE):
                break

        return last_decision  # type: ignore[return-value]

    def __repr__(self) -> str:
        stages = " → ".join(c.name for c in self.cogs)
        return f"CogPipeline(name={self.name!r}, stages=[{stages}])"


class CogComposer:
    """
    Constructs CogPipeline instances from named cogs in a CogRegistry.

    Usage::

        composer = CogComposer(registry)
        pipeline = composer.compose("intake-pipeline", ["intake", "compliance", "audit"])
        decision = pipeline.run(signal)
    """

    def __init__(self, registry: "CogRegistry") -> None:
        self.registry = registry

    def compose(self, name: str, cog_names: list[str]) -> CogPipeline:
        """
        Build a CogPipeline from an ordered list of registered cog names.

        Parameters:
            name:      Human-readable pipeline name.
            cog_names: Ordered names of cogs to include (resolved via registry).

        Returns:
            CogPipeline ready to process signals.
        """
        cogs = [self.registry.get(n) for n in cog_names]
        return CogPipeline(name=name, cogs=cogs)
