"""HarmAssessor — evaluates potential harm before a decision is executed."""

from __future__ import annotations

from typing import Callable

from cog.core.signal import InterpretedSignal
from cog.models.context import Context
from cog.models.decision import ReasoningChain
from cog.models.assessment import HarmAssessment, RiskLevel, Verdict
from cog.exceptions import HarmAssessmentError


class HarmAssessor:
    """
    Evaluates the harm potential of an interpreted signal within its context
    and the established reasoning chain.

    COG's third principle is: *assess harm before execution*. This component
    runs a configurable set of rules to produce a HarmAssessment that the
    ExecutionGate uses to allow, warn, escalate, or block execution.

    Rules are registered as callables with the signature::

        def rule(
            interpreted: InterpretedSignal,
            context: Context,
            chain: ReasoningChain,
            assessment: HarmAssessment,
        ) -> None:
            ...

    Each rule may raise ``assessment.risk_level``, append to
    ``assessment.identified_risks`` / ``assessment.mitigations``, or set
    ``assessment.verdict`` directly.

    .. note::
        The concrete rule implementations used in production are not
        publicly disclosed. See repository status notice.

    Usage::

        assessor = HarmAssessor()

        @assessor.rule
        def my_rule(interpreted, context, chain, assessment):
            if interpreted.annotations.get("destructive"):
                assessment.identified_risks.append("Destructive signal detected.")
                assessment.risk_level = RiskLevel.HIGH

        assessment = assessor.assess(interpreted, context, chain)
    """

    def __init__(self) -> None:
        self._rules: list[Callable] = []

    # ------------------------------------------------------------------
    # Rule registration
    # ------------------------------------------------------------------

    def rule(self, fn: Callable) -> Callable:
        """Decorator: register a harm assessment rule."""
        self._rules.append(fn)
        return fn

    def add_rule(self, fn: Callable) -> None:
        """Programmatically register a harm assessment rule."""
        self._rules.append(fn)

    # ------------------------------------------------------------------
    # Core operation
    # ------------------------------------------------------------------

    def assess(
        self,
        interpreted: InterpretedSignal,
        context: Context,
        chain: ReasoningChain,
    ) -> HarmAssessment:
        """
        Run all registered rules and return a HarmAssessment.

        Rules execute in registration order. The verdict is derived from the
        final risk level unless a rule sets it directly.

        Raises:
            HarmAssessmentError: if any rule raises an exception.
        """
        assessment = HarmAssessment(risk_level=RiskLevel.NONE)

        try:
            for rule_fn in self._rules:
                rule_fn(interpreted, context, chain, assessment)
        except Exception as exc:
            raise HarmAssessmentError(
                f"Harm assessment failed for signal {interpreted.signal.id!r}: {exc}"
            ) from exc

        # Derive verdict from final risk level if not explicitly set by a rule
        if assessment.verdict == Verdict.PROCEED:
            assessment.verdict = self._derive_verdict(assessment.risk_level)

        if assessment.identified_risks:
            assessment.notes = (
                f"{len(assessment.identified_risks)} risk(s) identified. "
                f"Verdict: {assessment.verdict.value}."
            )
        else:
            assessment.notes = "No risks identified. Signal is safe to proceed."

        return assessment

    # ------------------------------------------------------------------
    # Verdict derivation
    # ------------------------------------------------------------------

    def _derive_verdict(self, risk_level: RiskLevel) -> Verdict:
        """
        Map a risk level to the default execution verdict.

        The precise mapping is implementation-defined and may be overridden
        by registering a rule that sets ``assessment.verdict`` directly.
        """
        mapping: dict[RiskLevel, Verdict] = {
            RiskLevel.NONE: Verdict.PROCEED,
            RiskLevel.LOW: Verdict.PROCEED,
            RiskLevel.MEDIUM: Verdict.CAUTION,
            RiskLevel.HIGH: Verdict.ESCALATE,
            RiskLevel.CRITICAL: Verdict.BLOCK,
        }
        return mapping.get(risk_level, Verdict.BLOCK)
