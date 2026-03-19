"""CogEngine — the main orchestrator of a single COG governance pipeline."""

from __future__ import annotations

from cog.core.context import ContextManager
from cog.core.signal import SignalInterpreter
from cog.core.reasoning import ReasoningBuilder
from cog.core.harm import HarmAssessor
from cog.core.gate import ExecutionGate
from cog.models.signal import Signal
from cog.models.decision import Decision
from cog.utils.audit import AuditLogger


class CogEngine:
    """
    Orchestrates the full COG governance pipeline for a single decision unit.

    Pipeline stages (in order):

    1. **Context restoration** — ContextManager rebuilds situational awareness.
    2. **Signal interpretation** — SignalInterpreter derives intent and annotations.
    3. **Reasoning construction** — ReasoningBuilder produces the auditable chain.
    4. **Harm assessment** — HarmAssessor evaluates risk and recommends a verdict.
    5. **Execution gate** — ExecutionGate applies final policies and emits a Decision.

    Each stage is fully replaceable via dependency injection, allowing teams to
    plug in domain-specific implementations for any component.

    Usage::

        engine = CogEngine(name="my-cog")
        decision = engine.process(signal)

    Parameters:
        name:           Human-readable name for this COG instance.
        context_manager: Provides situational context.
        interpreter:    Interprets the raw signal.
        reasoning:      Builds the auditable reasoning chain.
        assessor:       Evaluates harm potential.
        gate:           Applies final policies and produces the Decision.
        audit_logger:   Records every decision for compliance / traceability.
    """

    def __init__(
        self,
        name: str = "default",
        context_manager: ContextManager | None = None,
        interpreter: SignalInterpreter | None = None,
        reasoning: ReasoningBuilder | None = None,
        assessor: HarmAssessor | None = None,
        gate: ExecutionGate | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self.name = name
        self.context_manager = context_manager or ContextManager()
        self.interpreter = interpreter or SignalInterpreter()
        self.reasoning = reasoning or ReasoningBuilder()
        self.assessor = assessor or HarmAssessor()
        self.gate = gate or ExecutionGate(cog_name=name)
        self.audit_logger = audit_logger or AuditLogger(cog_name=name)

        # Keep gate cog_name in sync
        self.gate.cog_name = self.name

    # ------------------------------------------------------------------
    # Core operation
    # ------------------------------------------------------------------

    def process(self, signal: Signal) -> Decision:
        """
        Run *signal* through the full COG governance pipeline.

        Returns:
            Decision: The authoritative governance outcome, fully auditable.
        """
        # Stage 1: Restore context
        context = self.context_manager.restore(signal)

        # Stage 2: Interpret signal
        interpreted = self.interpreter.interpret(signal, context)

        # Stage 3: Build reasoning chain
        chain = self.reasoning.build(interpreted, context)

        # Stage 4: Assess harm
        assessment = self.assessor.assess(interpreted, context, chain)

        # Stage 5: Gate execution
        decision = self.gate.evaluate(interpreted, context, chain, assessment)

        # Audit
        self.audit_logger.record(decision)

        return decision

    def __repr__(self) -> str:
        return f"CogEngine(name={self.name!r})"
