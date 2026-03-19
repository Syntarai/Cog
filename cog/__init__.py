"""
COG Verse System
================
A decision-governance layer that restores context before action.
Forces systems to interpret signals, expose reasoning, and assess harm
before execution — preventing uncontextualised and unsafe decisions
in high-stakes environments.
"""

from cog.verse.verse import CogVerse
from cog.core.engine import CogEngine
from cog.models.signal import Signal
from cog.models.context import Context
from cog.models.assessment import HarmAssessment, RiskLevel, Verdict
from cog.models.decision import Decision, ReasoningStep, ReasoningChain
from cog.exceptions import (
    CogError,
    ContextRestorationError,
    SignalInterpretationError,
    HarmAssessmentError,
    ExecutionBlockedError,
    CogNotFoundError,
)

__all__ = [
    "CogVerse",
    "CogEngine",
    "Signal",
    "Context",
    "HarmAssessment",
    "RiskLevel",
    "Verdict",
    "Decision",
    "ReasoningStep",
    "ReasoningChain",
    "CogError",
    "ContextRestorationError",
    "SignalInterpretationError",
    "HarmAssessmentError",
    "ExecutionBlockedError",
    "CogNotFoundError",
]
