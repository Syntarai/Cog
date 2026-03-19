"""ExecutionGate — the final checkpoint before an action is allowed to run."""

from __future__ import annotations

from typing import Any, Callable

from cog.core.signal import InterpretedSignal
from cog.models.context import Context
from cog.models.decision import ReasoningChain, Decision
from cog.models.assessment import HarmAssessment, Verdict
from cog.exceptions import ExecutionBlockedError


class ExecutionGate:
    """
    The final checkpoint in the COG governance pipeline.

    The gate consults the HarmAssessment and applies any registered
    gate policies before producing the final Decision. It may:

    - Allow execution (PROCEED / CAUTION)
    - Escalate to a human handler (ESCALATE)
    - Block execution entirely (BLOCK)

    Registered policies run after the harm assessment verdict is set.
    Each policy may override the verdict or attach additional metadata.

    Usage::

        gate = ExecutionGate()

        @gate.policy
        def require_approval_in_prod(interpreted, context, assessment, decision):
            if context.environment == "production" and decision.verdict == Verdict.CAUTION:
                decision.verdict = Verdict.ESCALATE

        decision = gate.evaluate(interpreted, context, chain, assessment)

    Parameters:
        cog_name:         Identifier embedded in produced Decisions.
        on_block:         Optional callback invoked when a signal is blocked.
        on_escalate:      Optional callback invoked when a signal is escalated.
        raise_on_block:   If True, raise ExecutionBlockedError instead of
                          returning a BLOCK Decision.
    """

    def __init__(
        self,
        cog_name: str = "default",
        on_block: Callable[[Decision], None] | None = None,
        on_escalate: Callable[[Decision], None] | None = None,
        raise_on_block: bool = False,
    ) -> None:
        self.cog_name = cog_name
        self.on_block = on_block
        self.on_escalate = on_escalate
        self.raise_on_block = raise_on_block
        self._policies: list[Callable] = []

    # ------------------------------------------------------------------
    # Policy registration
    # ------------------------------------------------------------------

    def policy(self, fn: Callable) -> Callable:
        """Decorator: register a gate policy."""
        self._policies.append(fn)
        return fn

    def add_policy(self, fn: Callable) -> None:
        """Programmatically register a gate policy."""
        self._policies.append(fn)

    # ------------------------------------------------------------------
    # Core operation
    # ------------------------------------------------------------------

    def evaluate(
        self,
        interpreted: InterpretedSignal,
        context: Context,
        chain: ReasoningChain,
        assessment: HarmAssessment,
    ) -> Decision:
        """
        Produce the final Decision for this governance cycle.

        Raises:
            ExecutionBlockedError: if raise_on_block is True and the
                verdict resolves to BLOCK.
        """
        action: Any = None
        if assessment.is_safe:
            action = interpreted.normalised

        decision = Decision(
            signal=interpreted.signal,
            context=context,
            reasoning=chain,
            assessment=assessment,
            verdict=assessment.verdict,
            action=action,
            cog_name=self.cog_name,
        )

        # Run registered gate policies (may override verdict)
        for policy_fn in self._policies:
            policy_fn(interpreted, context, assessment, decision)

        # Post-policy callbacks
        if decision.verdict == Verdict.BLOCK:
            if self.on_block:
                self.on_block(decision)
            if self.raise_on_block:
                raise ExecutionBlockedError(
                    f"Execution blocked for signal {interpreted.signal.id!r}. "
                    f"Risks: {assessment.identified_risks}",
                    risk_level=assessment.risk_level.value,
                    risks=assessment.identified_risks,
                )

        if decision.verdict == Verdict.ESCALATE and self.on_escalate:
            self.on_escalate(decision)

        return decision
