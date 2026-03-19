"""Tests for the COG Verse system."""

import pytest
from cog.models.signal import Signal
from cog.models.assessment import Verdict, RiskLevel
from cog.verse.verse import CogVerse
from cog.verse.registry import CogRegistry
from cog.verse.composer import CogComposer, CogPipeline
from cog.core.engine import CogEngine
from cog.exceptions import CogNotFoundError, PipelineError


def make_signal(**kwargs) -> Signal:
    defaults = {"type": "query", "payload": {"q": "status"}, "source": "monitor"}
    return Signal(**{**defaults, **kwargs})


# ---------------------------------------------------------------------------
# CogRegistry
# ---------------------------------------------------------------------------

class TestCogRegistry:
    def test_register_and_get(self):
        registry = CogRegistry()
        engine = CogEngine(name="reg-test")
        registry.register("reg-test", engine)
        assert registry.get("reg-test") is engine

    def test_has(self):
        registry = CogRegistry()
        registry.register("x", CogEngine(name="x"))
        assert registry.has("x")
        assert not registry.has("y")

    def test_get_missing_raises(self):
        registry = CogRegistry()
        with pytest.raises(CogNotFoundError):
            registry.get("missing")

    def test_unregister(self):
        registry = CogRegistry()
        registry.register("tmp", CogEngine(name="tmp"))
        registry.unregister("tmp")
        assert not registry.has("tmp")

    def test_names(self):
        registry = CogRegistry()
        registry.register("a", CogEngine(name="a"))
        registry.register("b", CogEngine(name="b"))
        assert set(registry.names()) == {"a", "b"}

    def test_len(self):
        registry = CogRegistry()
        assert len(registry) == 0
        registry.register("one", CogEngine(name="one"))
        assert len(registry) == 1


# ---------------------------------------------------------------------------
# CogComposer / CogPipeline
# ---------------------------------------------------------------------------

class TestCogComposer:
    def _registry_with_cogs(self, *names):
        registry = CogRegistry()
        for name in names:
            registry.register(name, CogEngine(name=name))
        return registry

    def test_compose_returns_pipeline(self):
        registry = self._registry_with_cogs("a", "b")
        composer = CogComposer(registry)
        pipeline = composer.compose("test-pipe", ["a", "b"])
        assert isinstance(pipeline, CogPipeline)
        assert len(pipeline.cogs) == 2

    def test_compose_missing_cog_raises(self):
        registry = self._registry_with_cogs("a")
        composer = CogComposer(registry)
        with pytest.raises(CogNotFoundError):
            composer.compose("bad", ["a", "missing"])

    def test_pipeline_run_returns_decision(self):
        registry = self._registry_with_cogs("s1", "s2")
        composer = CogComposer(registry)
        pipeline = composer.compose("run-test", ["s1", "s2"])
        decision = pipeline.run(make_signal())
        assert decision is not None

    def test_empty_pipeline_raises(self):
        pipeline = CogPipeline(name="empty", cogs=[])
        with pytest.raises(PipelineError):
            pipeline.run(make_signal())

    def test_pipeline_stops_on_block(self):
        """Pipeline should stop early when a stage blocks."""
        from cog.core.harm import HarmAssessor
        from cog.models.assessment import HarmAssessment

        blocking_assessor = HarmAssessor()

        @blocking_assessor.rule
        def always_block(interpreted, context, chain, assessment):
            assessment.risk_level = RiskLevel.CRITICAL

        blocker = CogEngine(name="blocker", assessor=blocking_assessor)
        after = CogEngine(name="after")

        registry = CogRegistry()
        registry.register("blocker", blocker)
        registry.register("after", after)

        composer = CogComposer(registry)
        pipeline = composer.compose("stop-test", ["blocker", "after"])
        decision = pipeline.run(make_signal())

        # Should have stopped at "blocker", so cog_name is "blocker"
        assert decision.cog_name == "blocker"
        assert decision.verdict == Verdict.BLOCK


# ---------------------------------------------------------------------------
# CogVerse
# ---------------------------------------------------------------------------

class TestCogVerse:
    def test_add_cog_and_process(self):
        verse = CogVerse(default_environment="test")
        verse.add_cog("main")
        decision = verse.process(make_signal(), cog_name="main")
        assert decision is not None

    def test_default_cog_auto_created(self):
        verse = CogVerse()
        decision = verse.process(make_signal())
        assert decision is not None

    def test_process_unknown_cog_raises(self):
        verse = CogVerse()
        with pytest.raises(CogNotFoundError):
            verse.process(make_signal(), cog_name="ghost")

    def test_process_through_pipeline(self):
        verse = CogVerse()
        verse.add_cog("gate-1")
        verse.add_cog("gate-2")
        decision = verse.process_through(make_signal(), ["gate-1", "gate-2"])
        assert decision is not None

    def test_build_pipeline_reusable(self):
        verse = CogVerse()
        verse.add_cog("p1")
        verse.add_cog("p2")
        pipeline = verse.build_pipeline("reuse", ["p1", "p2"])
        assert isinstance(pipeline, CogPipeline)
        d1 = pipeline.run(make_signal())
        d2 = pipeline.run(make_signal())
        assert d1 is not d2

    def test_cog_names(self):
        verse = CogVerse()
        verse.add_cog("x")
        verse.add_cog("y")
        assert set(verse.cog_names()) == {"x", "y"}

    def test_register_prebuilt_cog(self):
        verse = CogVerse()
        engine = CogEngine(name="external")
        verse.register_cog("external", engine)
        assert verse.registry.has("external")

    def test_remove_cog(self):
        verse = CogVerse()
        verse.add_cog("temp")
        verse.remove_cog("temp")
        assert not verse.registry.has("temp")
