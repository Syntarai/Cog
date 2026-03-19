"""Custom exceptions for the COG Verse System."""


class CogError(Exception):
    """Base exception for all COG errors."""


class ContextRestorationError(CogError):
    """Raised when context cannot be restored for a signal."""


class SignalInterpretationError(CogError):
    """Raised when a signal cannot be interpreted."""


class HarmAssessmentError(CogError):
    """Raised when harm assessment fails."""


class ExecutionBlockedError(CogError):
    """Raised when execution is blocked due to harm assessment."""

    def __init__(self, message: str, risk_level: str, risks: list[str]) -> None:
        super().__init__(message)
        self.risk_level = risk_level
        self.risks = risks


class CogNotFoundError(CogError):
    """Raised when a named COG is not found in the verse registry."""

    def __init__(self, name: str) -> None:
        super().__init__(f"COG '{name}' not found in the verse registry.")
        self.name = name


class PipelineError(CogError):
    """Raised when a composed COG pipeline fails."""
