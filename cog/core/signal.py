"""SignalInterpreter — derives meaning from a raw signal given its context."""

from __future__ import annotations

from typing import Any, Callable

from cog.models.signal import Signal
from cog.models.context import Context
from cog.exceptions import SignalInterpretationError


class InterpretedSignal:
    """
    A signal enriched with derived intent, normalised payload, and annotations.

    Attributes:
        signal:      The original raw signal.
        context:     The restored context.
        intent:      Human-readable description of the interpreted intent.
        normalised:  Canonicalised version of the payload.
        annotations: Key-value enrichments added by interpreters.
        confidence:  Interpretation confidence in [0.0, 1.0].
    """

    def __init__(
        self,
        signal: Signal,
        context: Context,
        intent: str = "",
        normalised: Any = None,
        annotations: dict[str, Any] | None = None,
        confidence: float = 1.0,
    ) -> None:
        self.signal = signal
        self.context = context
        self.intent = intent
        self.normalised = normalised if normalised is not None else signal.payload
        self.annotations: dict[str, Any] = annotations or {}
        self.confidence = confidence

    def annotate(self, key: str, value: Any) -> None:
        """Add or update an annotation."""
        self.annotations[key] = value

    def __repr__(self) -> str:
        return (
            f"InterpretedSignal(type={self.signal.type!r}, "
            f"intent={self.intent!r}, confidence={self.confidence:.2f})"
        )


class SignalInterpreter:
    """
    Interprets incoming signals in the context of the restored situational picture.

    Interpreters are layered: each registered handler may enrich the
    InterpretedSignal. The chain runs in registration order.

    Usage::

        interpreter = SignalInterpreter()

        @interpreter.handler("delete")
        def handle_delete(signal, context, interpreted):
            interpreted.intent = "Permanently remove resource"
            interpreted.annotate("destructive", True)

        result = interpreter.interpret(signal, context)
    """

    def __init__(self, default_intent: str = "Unspecified action") -> None:
        self.default_intent = default_intent
        self._handlers: dict[str, list[Callable]] = {}
        self._global_handlers: list[Callable] = []

    # ------------------------------------------------------------------
    # Handler registration
    # ------------------------------------------------------------------

    def handler(
        self, signal_type: str
    ) -> Callable[[Callable], Callable]:
        """Decorator: register a handler for a specific signal type."""

        def decorator(fn: Callable) -> Callable:
            self._handlers.setdefault(signal_type, []).append(fn)
            return fn

        return decorator

    def global_handler(self, fn: Callable) -> Callable:
        """Decorator: register a handler that runs for every signal type."""
        self._global_handlers.append(fn)
        return fn

    def add_handler(self, signal_type: str, fn: Callable) -> None:
        """Programmatically register a handler for a specific signal type."""
        self._handlers.setdefault(signal_type, []).append(fn)

    def add_global_handler(self, fn: Callable) -> None:
        """Programmatically register a global handler."""
        self._global_handlers.append(fn)

    # ------------------------------------------------------------------
    # Core operation
    # ------------------------------------------------------------------

    def interpret(self, signal: Signal, context: Context) -> InterpretedSignal:
        """
        Return an InterpretedSignal for *signal* given *context*.

        Runs all global handlers first, then type-specific handlers.

        Raises:
            SignalInterpretationError: if any handler raises.
        """
        interpreted = InterpretedSignal(
            signal=signal,
            context=context,
            intent=self.default_intent,
        )

        try:
            for handler in self._global_handlers:
                handler(signal, context, interpreted)

            for handler in self._handlers.get(signal.type, []):
                handler(signal, context, interpreted)
        except Exception as exc:
            raise SignalInterpretationError(
                f"Interpretation failed for signal {signal.id!r}: {exc}"
            ) from exc

        return interpreted
