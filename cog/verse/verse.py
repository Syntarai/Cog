"""CogVerse — the top-level universe of interacting COG governance units."""

from __future__ import annotations

from typing import Any

from cog.core.engine import CogEngine
from cog.core.context import ContextManager
from cog.core.signal import SignalInterpreter
from cog.core.reasoning import ReasoningBuilder
from cog.core.harm import HarmAssessor
from cog.core.gate import ExecutionGate
from cog.verse.registry import CogRegistry
from cog.verse.composer import CogComposer, CogPipeline
from cog.models.signal import Signal
from cog.models.decision import Decision
from cog.utils.audit import AuditLogger
from cog.exceptions import CogNotFoundError


class CogVerse:
    """
    The central entry point for the COG Verse System.

    A CogVerse manages a registry of named CogEngines (the "cogs" of the
    verse) and a composer that assembles them into multi-stage governance
    pipelines. It is the primary interface through which host applications
    submit signals for governance.

    Quick start::

        verse = CogVerse()
        verse.add_cog("main")
        decision = verse.process(signal)

    Advanced — compose a multi-stage pipeline::

        verse = CogVerse()
        verse.add_cog("intake", environment="edge")
        verse.add_cog("compliance", environment="production")
        verse.add_cog("audit", environment="production")

        decision = verse.process_through(signal, ["intake", "compliance", "audit"])
    """

    def __init__(self, default_environment: str = "default") -> None:
        self.default_environment = default_environment
        self.registry = CogRegistry()
        self.composer = CogComposer(self.registry)

    # ------------------------------------------------------------------
    # COG management
    # ------------------------------------------------------------------

    def add_cog(
        self,
        name: str,
        *,
        environment: str | None = None,
        context_manager: ContextManager | None = None,
        interpreter: SignalInterpreter | None = None,
        reasoning: ReasoningBuilder | None = None,
        assessor: HarmAssessor | None = None,
        gate: ExecutionGate | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> CogEngine:
        """
        Create and register a new CogEngine under *name*.

        All component arguments are optional; defaults are used for any
        component not explicitly provided.

        Returns:
            The newly created CogEngine.
        """
        env = environment or self.default_environment
        cm = context_manager or ContextManager(environment=env)
        engine = CogEngine(
            name=name,
            context_manager=cm,
            interpreter=interpreter,
            reasoning=reasoning,
            assessor=assessor,
            gate=gate,
            audit_logger=audit_logger,
        )
        self.registry.register(name, engine)
        return engine

    def register_cog(self, name: str, cog: CogEngine) -> None:
        """Register a pre-built CogEngine under *name*."""
        self.registry.register(name, cog)

    def get_cog(self, name: str) -> CogEngine:
        """Return the registered CogEngine for *name*.

        Raises:
            CogNotFoundError: if not found.
        """
        return self.registry.get(name)

    def remove_cog(self, name: str) -> None:
        """Remove a cog from the verse. No-op if not found."""
        self.registry.unregister(name)

    # ------------------------------------------------------------------
    # Signal processing
    # ------------------------------------------------------------------

    def process(self, signal: Signal, cog_name: str = "default") -> Decision:
        """
        Process *signal* through the named cog.

        If no *cog_name* is provided and a "default" cog exists, it is used.
        If "default" does not exist, one is created automatically.

        Returns:
            The governance Decision.
        """
        if not self.registry.has(cog_name):
            if cog_name == "default":
                self.add_cog("default")
            else:
                raise CogNotFoundError(cog_name)

        return self.registry.get(cog_name).process(signal)

    def process_through(
        self, signal: Signal, cog_names: list[str], pipeline_name: str = "ad-hoc"
    ) -> Decision:
        """
        Process *signal* through an ordered multi-cog pipeline.

        The pipeline halts early on BLOCK or ESCALATE verdicts.

        Parameters:
            signal:        Signal to govern.
            cog_names:     Ordered list of registered cog names.
            pipeline_name: Human-readable label for this pipeline run.

        Returns:
            Decision from the last executed pipeline stage.
        """
        pipeline = self.composer.compose(pipeline_name, cog_names)
        return pipeline.run(signal)

    def build_pipeline(self, name: str, cog_names: list[str]) -> CogPipeline:
        """
        Build and return a reusable CogPipeline without executing it.

        Parameters:
            name:      Pipeline name.
            cog_names: Ordered list of registered cog names.

        Returns:
            CogPipeline ready to call `.run(signal)` on.
        """
        return self.composer.compose(name, cog_names)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def cog_names(self) -> list[str]:
        """Return names of all registered cogs."""
        return self.registry.names()

    def __repr__(self) -> str:
        return f"CogVerse(environment={self.default_environment!r}, cogs={self.cog_names()})"
