"""Tests for COG core components."""

import pytest
from cog.models.signal import Signal
from cog.models.context import Context
from cog.models.assessment import RiskLevel, Verdict
from cog.core.context import ContextManager
from cog.core.signal import SignalInterpreter
from cog.core.reasoning import ReasoningBuilder
from cog.core.harm import HarmAssessor
from cog.core.gate import ExecutionGate
from cog.core.engine import CogEngine
from cog.exceptions import (
    ContextRestorationError,
    SignalInterpretationError,
    HarmAssessmentError,
    ExecutionBlockedError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_signal(**kwargs) -> Signal:
    defaults = {"type": "action", "payload": {"op": "read"}, "source": "test-agent"}
    return Signal(**{**defaults, **kwargs})


# ---------------------------------------------------------------------------
# ContextManager
# ---------------------------------------------------------------------------

class TestContextManager:
    def test_basic_restore(self):
        mgr = ContextManager(environment="staging")
        sig = make_signal()
        ctx = mgr.restore(sig)
        assert ctx.environment == "staging"

    def test_state_provider(self):
        mgr = ContextManager()
        mgr.add_state_provider(lambda s: {"user": "admin"})
        ctx = mgr.restore(make_signal())
        assert ctx.state["user"] == "admin"

    def test_constraint_provider(self):
        mgr = ContextManager()
        mgr.add_constraint_provider(lambda s: ["no-delete"])
        ctx = mgr.restore(make_signal())
        assert "no-delete" in ctx.constraints

    def test_default_constraints_always_present(self):
        mgr = ContextManager(default_constraints=["always-on"])
        ctx = mgr.restore(make_signal())
        assert "always-on" in ctx.constraints

    def test_history_accumulates(self):
        mgr = ContextManager()
        mgr.restore(make_signal())
        mgr.restore(make_signal())
        ctx = mgr.restore(make_signal())
        assert len(ctx.history) == 2  # previous two signals

    def test_provider_exception_raises_context_error(self):
        mgr = ContextManager()

        def bad_provider(sig):
            raise RuntimeError("provider failure")

        mgr.add_state_provider(bad_provider)
        with pytest.raises(ContextRestorationError):
            mgr.restore(make_signal())

    def test_clear_history(self):
        mgr = ContextManager()
        mgr.restore(make_signal())
        mgr.clear_history()
        ctx = mgr.restore(make_signal())
        assert ctx.history == []


# ---------------------------------------------------------------------------
# SignalInterpreter
# ---------------------------------------------------------------------------

class TestSignalInterpreter:
    def test_default_intent(self):
        interp = SignalInterpreter(default_intent="Default")
        ctx = Context(environment="test")
        result = interp.interpret(make_signal(), ctx)
        assert result.intent == "Default"

    def test_type_specific_handler(self):
        interp = SignalInterpreter()
        ctx = Context(environment="test")

        @interp.handler("action")
        def handle(sig, context, interpreted):
            interpreted.intent = "Handled action"

        result = interp.interpret(make_signal(type="action"), ctx)
        assert result.intent == "Handled action"

    def test_global_handler_runs_for_all_types(self):
        interp = SignalInterpreter()
        ctx = Context(environment="test")
        seen = []

        @interp.global_handler
        def capture(sig, context, interpreted):
            seen.append(sig.type)

        interp.interpret(make_signal(type="query"), ctx)
        interp.interpret(make_signal(type="command"), ctx)
        assert "query" in seen
        assert "command" in seen

    def test_annotation(self):
        interp = SignalInterpreter()
        ctx = Context(environment="test")
        interp.add_handler("action", lambda s, c, i: i.annotate("flagged", True))
        result = interp.interpret(make_signal(type="action"), ctx)
        assert result.annotations["flagged"] is True

    def test_handler_exception_raises_signal_error(self):
        interp = SignalInterpreter()
        ctx = Context(environment="test")

        def bad(sig, context, interpreted):
            raise ValueError("oops")

        interp.add_handler("action", bad)
        with pytest.raises(SignalInterpretationError):
            interp.interpret(make_signal(type="action"), ctx)


# ---------------------------------------------------------------------------
# ReasoningBuilder
# ---------------------------------------------------------------------------

class TestReasoningBuilder:
    def test_default_steps_present(self):
        builder = ReasoningBuilder()
        interp = SignalInterpreter().interpret(make_signal(), Context(environment="test"))
        chain = builder.build(interp, Context(environment="test"))
        # Built-in: source trust, constraint check, intent classification
        assert len(chain.steps) >= 3

    def test_conclusion_is_set(self):
        builder = ReasoningBuilder()
        interp = SignalInterpreter().interpret(make_signal(), Context(environment="test"))
        chain = builder.build(interp, Context(environment="test"))
        assert chain.conclusion

    def test_custom_step_appended(self):
        builder = ReasoningBuilder()

        @builder.step("custom check")
        def custom(interpreted, ctx, chain):
            chain.add_step("extra step", output="done")

        interp = SignalInterpreter().interpret(make_signal(), Context(environment="test"))
        chain = builder.build(interp, Context(environment="test"))
        descriptions = [s.description for s in chain.steps]
        assert "extra step" in descriptions


# ---------------------------------------------------------------------------
# HarmAssessor
# ---------------------------------------------------------------------------

class TestHarmAssessor:
    def test_no_rules_returns_none_risk(self):
        assessor = HarmAssessor()
        interp = SignalInterpreter().interpret(make_signal(), Context(environment="test"))
        chain = ReasoningBuilder().build(interp, Context(environment="test"))
        assessment = assessor.assess(interp, Context(environment="test"), chain)
        assert assessment.risk_level == RiskLevel.NONE
        assert assessment.verdict == Verdict.PROCEED

    def test_custom_rule_elevates_risk(self):
        assessor = HarmAssessor()

        @assessor.rule
        def block_all(interpreted, context, chain, assessment):
            assessment.risk_level = RiskLevel.CRITICAL
            assessment.identified_risks.append("Always block in test.")

        interp = SignalInterpreter().interpret(make_signal(), Context(environment="test"))
        chain = ReasoningBuilder().build(interp, Context(environment="test"))
        assessment = assessor.assess(interp, Context(environment="test"), chain)
        assert assessment.risk_level == RiskLevel.CRITICAL
        assert assessment.verdict == Verdict.BLOCK

    def test_rule_exception_raises_assessment_error(self):
        assessor = HarmAssessor()
        assessor.add_rule(lambda i, c, ch, a: (_ for _ in ()).throw(RuntimeError("boom")))
        interp = SignalInterpreter().interpret(make_signal(), Context(environment="test"))
        chain = ReasoningBuilder().build(interp, Context(environment="test"))
        with pytest.raises(HarmAssessmentError):
            assessor.assess(interp, Context(environment="test"), chain)


# ---------------------------------------------------------------------------
# ExecutionGate
# ---------------------------------------------------------------------------

class TestExecutionGate:
    def _build_safe_inputs(self):
        sig = make_signal()
        ctx = Context(environment="test")
        interp = SignalInterpreter().interpret(sig, ctx)
        chain = ReasoningBuilder().build(interp, ctx)
        from cog.models.assessment import HarmAssessment
        assessment = HarmAssessment(risk_level=RiskLevel.NONE, verdict=Verdict.PROCEED)
        return interp, ctx, chain, assessment

    def test_safe_signal_approved(self):
        gate = ExecutionGate()
        interp, ctx, chain, assessment = self._build_safe_inputs()
        decision = gate.evaluate(interp, ctx, chain, assessment)
        assert decision.approved
        assert decision.verdict == Verdict.PROCEED

    def test_block_raises_when_configured(self):
        gate = ExecutionGate(raise_on_block=True)
        interp, ctx, chain, _ = self._build_safe_inputs()
        from cog.models.assessment import HarmAssessment
        assessment = HarmAssessment(risk_level=RiskLevel.CRITICAL, verdict=Verdict.BLOCK)
        with pytest.raises(ExecutionBlockedError):
            gate.evaluate(interp, ctx, chain, assessment)

    def test_on_block_callback_called(self):
        called = []
        gate = ExecutionGate(on_block=lambda d: called.append(d))
        interp, ctx, chain, _ = self._build_safe_inputs()
        from cog.models.assessment import HarmAssessment
        assessment = HarmAssessment(risk_level=RiskLevel.CRITICAL, verdict=Verdict.BLOCK)
        gate.evaluate(interp, ctx, chain, assessment)
        assert len(called) == 1

    def test_policy_can_override_verdict(self):
        gate = ExecutionGate()

        @gate.policy
        def always_escalate(interpreted, context, assessment, decision):
            decision.verdict = Verdict.ESCALATE

        interp, ctx, chain, assessment = self._build_safe_inputs()
        decision = gate.evaluate(interp, ctx, chain, assessment)
        assert decision.verdict == Verdict.ESCALATE


# ---------------------------------------------------------------------------
# CogEngine (integration)
# ---------------------------------------------------------------------------

class TestCogEngine:
    def test_process_returns_decision(self):
        engine = CogEngine(name="test-engine")
        sig = make_signal()
        decision = engine.process(sig)
        assert decision.signal.id == sig.id
        assert decision.cog_name == "test-engine"

    def test_decision_is_audited(self):
        engine = CogEngine(name="audited")
        engine.process(make_signal())
        assert len(engine.audit_logger.records) == 1

    def test_decision_summary_contains_verdict(self):
        engine = CogEngine(name="summary-test")
        decision = engine.process(make_signal())
        summary = decision.summary()
        assert "PROCEED" in summary or "CAUTION" in summary or "BLOCK" in summary
