"""Tests for COG data models."""

import pytest
from cog.models.signal import Signal
from cog.models.context import Context
from cog.models.assessment import HarmAssessment, RiskLevel, Verdict
from cog.models.decision import Decision, ReasoningChain, ReasoningStep


# ---------------------------------------------------------------------------
# Signal
# ---------------------------------------------------------------------------

class TestSignal:
    def test_basic_creation(self):
        sig = Signal(type="action", payload={"op": "read"}, source="agent-1")
        assert sig.type == "action"
        assert sig.source == "agent-1"
        assert sig.priority == "normal"
        assert sig.id  # auto-generated

    def test_invalid_priority_raises(self):
        with pytest.raises(ValueError, match="Invalid priority"):
            Signal(type="action", payload={}, source="x", priority="urgent")

    def test_all_valid_priorities(self):
        for p in ("low", "normal", "high", "critical"):
            sig = Signal(type="cmd", payload=None, source="s", priority=p)
            assert sig.priority == p

    def test_unique_ids(self):
        s1 = Signal(type="x", payload=None, source="s")
        s2 = Signal(type="x", payload=None, source="s")
        assert s1.id != s2.id


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

class TestContext:
    def test_basic_creation(self):
        ctx = Context(environment="production")
        assert ctx.environment == "production"
        assert ctx.constraints == []
        assert ctx.history == []

    def test_add_constraint(self):
        ctx = Context(environment="test")
        ctx.add_constraint("no-delete")
        assert ctx.has_constraint("no-delete")
        # Adding again is idempotent
        ctx.add_constraint("no-delete")
        assert ctx.constraints.count("no-delete") == 1

    def test_add_history(self):
        ctx = Context(environment="dev")
        sig = Signal(type="query", payload={}, source="user")
        ctx.add_history(sig)
        assert sig in ctx.history


# ---------------------------------------------------------------------------
# HarmAssessment
# ---------------------------------------------------------------------------

class TestHarmAssessment:
    def test_is_safe_proceed(self):
        a = HarmAssessment(risk_level=RiskLevel.NONE, verdict=Verdict.PROCEED)
        assert a.is_safe

    def test_is_safe_caution(self):
        a = HarmAssessment(risk_level=RiskLevel.MEDIUM, verdict=Verdict.CAUTION)
        assert a.is_safe

    def test_not_safe_block(self):
        a = HarmAssessment(risk_level=RiskLevel.CRITICAL, verdict=Verdict.BLOCK)
        assert not a.is_safe

    def test_invalid_confidence_raises(self):
        with pytest.raises(ValueError):
            HarmAssessment(risk_level=RiskLevel.LOW, confidence=1.5)

    def test_risk_level_ordering(self):
        assert RiskLevel.HIGH > RiskLevel.MEDIUM
        assert RiskLevel.CRITICAL >= RiskLevel.CRITICAL
        assert not (RiskLevel.LOW > RiskLevel.HIGH)

    def test_risk_score_values(self):
        assert RiskLevel.NONE.score == 0.0
        assert RiskLevel.CRITICAL.score == 1.0


# ---------------------------------------------------------------------------
# ReasoningChain
# ---------------------------------------------------------------------------

class TestReasoningChain:
    def test_add_step(self):
        chain = ReasoningChain()
        step = chain.add_step("Check source", inputs={"src": "a"}, output=True)
        assert isinstance(step, ReasoningStep)
        assert step.index == 0
        assert len(chain.steps) == 1

    def test_step_index_increments(self):
        chain = ReasoningChain()
        chain.add_step("step 1")
        chain.add_step("step 2")
        assert chain.steps[0].index == 0
        assert chain.steps[1].index == 1
