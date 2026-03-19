"""ReasoningBuilder — constructs an auditable chain of reasoning for a decision."""

from __future__ import annotations

from typing import Callable

from cog.core.signal import InterpretedSignal
from cog.models.context import Context
from cog.models.decision import ReasoningChain, ReasoningStep


class ReasoningBuilder:
    """
    Constructs a transparent, step-by-step ReasoningChain from an
    interpreted signal and its context.

    COG's second principle is: *expose reasoning*. Every decision must
    carry an auditable record of how the conclusion was reached.

    Registered reasoning steps are called in order. Each step receives
    the current chain and may append new steps to it.

    Usage::

        builder = ReasoningBuilder()

        @builder.step("Check signal priority")
        def priority_step(interpreted, context, chain):
            chain.add_step(
                description="Signal priority assessed",
                inputs={"priority": interpreted.signal.priority},
                output=interpreted.signal.priority,
            )

        chain = builder.build(interpreted, context)
    """

    def __init__(self) -> None:
        self._steps: list[tuple[str, Callable]] = []

    # ------------------------------------------------------------------
    # Step registration
    # ------------------------------------------------------------------

    def step(self, name: str) -> Callable[[Callable], Callable]:
        """Decorator: register a reasoning step function."""

        def decorator(fn: Callable) -> Callable:
            self._steps.append((name, fn))
            return fn

        return decorator

    def add_step(self, name: str, fn: Callable) -> None:
        """Programmatically register a reasoning step."""
        self._steps.append((name, fn))

    # ------------------------------------------------------------------
    # Built-in default steps
    # ------------------------------------------------------------------

    @staticmethod
    def _step_source_trust(
        interpreted: InterpretedSignal, context: Context, chain: ReasoningChain
    ) -> None:
        """Assess whether the signal source is known and trusted."""
        source = interpreted.signal.source
        known = source in context.state.get("trusted_sources", [])
        chain.add_step(
            description="Source trust assessment",
            inputs={"source": source, "trusted_sources": context.state.get("trusted_sources", [])},
            output={"trusted": known},
            confidence=1.0,
        )

    @staticmethod
    def _step_constraint_check(
        interpreted: InterpretedSignal, context: Context, chain: ReasoningChain
    ) -> None:
        """Verify whether active constraints allow this signal type."""
        forbidden_types = [
            c.removeprefix("no-signal-type:")
            for c in context.constraints
            if c.startswith("no-signal-type:")
        ]
        blocked = interpreted.signal.type in forbidden_types
        chain.add_step(
            description="Active constraint check",
            inputs={
                "signal_type": interpreted.signal.type,
                "forbidden_types": forbidden_types,
            },
            output={"blocked_by_constraint": blocked},
            confidence=1.0,
        )

    @staticmethod
    def _step_intent_classification(
        interpreted: InterpretedSignal, context: Context, chain: ReasoningChain
    ) -> None:
        """Record the interpreted intent for audit purposes."""
        chain.add_step(
            description="Intent classification",
            inputs={"raw_type": interpreted.signal.type, "annotations": interpreted.annotations},
            output={"intent": interpreted.intent, "confidence": interpreted.confidence},
            confidence=interpreted.confidence,
        )

    # ------------------------------------------------------------------
    # Core operation
    # ------------------------------------------------------------------

    def build(
        self,
        interpreted: InterpretedSignal,
        context: Context,
    ) -> ReasoningChain:
        """
        Execute all registered reasoning steps and return the completed chain.

        Default built-in steps (source trust, constraint check, intent
        classification) always run first. Registered custom steps follow.
        """
        chain = ReasoningChain()

        # Built-in steps
        self._step_source_trust(interpreted, context, chain)
        self._step_constraint_check(interpreted, context, chain)
        self._step_intent_classification(interpreted, context, chain)

        # Custom registered steps
        for _name, fn in self._steps:
            fn(interpreted, context, chain)

        # Derive overall confidence as the mean of step confidences
        if chain.steps:
            chain.confidence = sum(s.confidence for s in chain.steps) / len(chain.steps)

        chain.conclusion = (
            f"Signal [{interpreted.signal.type}] from '{interpreted.signal.source}' "
            f"interpreted as: {interpreted.intent}. "
            f"Evaluated against {len(context.constraints)} constraint(s). "
            f"Overall reasoning confidence: {chain.confidence:.0%}."
        )

        return chain
