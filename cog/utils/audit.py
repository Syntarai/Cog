"""AuditLogger — immutable, append-only audit trail for all COG decisions."""

from __future__ import annotations

import json
import logging
from datetime import timezone
from typing import Any

from cog.models.decision import Decision

logger = logging.getLogger("cog.audit")


class AuditLogger:
    """
    Records every Decision produced by a CogEngine into an append-only log.

    The audit trail is critical for compliance, post-incident analysis, and
    demonstrating that every executed action passed through COG governance.

    Two backends are provided:
    - In-memory store (always active): `AuditLogger.records`
    - Python logger (always active): writes structured JSON to ``cog.audit``

    An optional file path can be provided to persist records to disk.

    Usage::

        audit = AuditLogger(cog_name="my-cog", log_file="/var/log/cog.jsonl")
        audit.record(decision)
        for entry in audit.records:
            print(entry["verdict"])

    Parameters:
        cog_name:  Name embedded in every audit entry.
        log_file:  Optional path to a JSONL file for persistent storage.
    """

    def __init__(self, cog_name: str = "default", log_file: str | None = None) -> None:
        self.cog_name = cog_name
        self.log_file = log_file
        self.records: list[dict[str, Any]] = []

    def record(self, decision: Decision) -> None:
        """Append *decision* to the audit log."""
        entry = self._serialise(decision)
        self.records.append(entry)
        logger.info(json.dumps(entry))
        if self.log_file:
            self._write_to_file(entry)

    def get_by_verdict(self, verdict: str) -> list[dict[str, Any]]:
        """Return all audit records matching the given verdict string."""
        return [r for r in self.records if r["verdict"] == verdict]

    def get_by_signal_id(self, signal_id: str) -> dict[str, Any] | None:
        """Return the audit record for a specific signal ID, or None."""
        for record in self.records:
            if record["signal_id"] == signal_id:
                return record
        return None

    def clear(self) -> None:
        """Flush the in-memory audit store (does not affect persisted files)."""
        self.records.clear()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _serialise(decision: Decision) -> dict[str, Any]:
        return {
            "decision_id": decision.id,
            "cog_name": decision.cog_name,
            "timestamp": decision.timestamp.astimezone(timezone.utc).isoformat(),
            "signal_id": decision.signal.id,
            "signal_type": decision.signal.type,
            "signal_source": decision.signal.source,
            "environment": decision.context.environment,
            "verdict": decision.verdict.value,
            "risk_level": decision.assessment.risk_level.value,
            "identified_risks": decision.assessment.identified_risks,
            "reasoning_steps": len(decision.reasoning.steps),
            "reasoning_conclusion": decision.reasoning.conclusion,
            "approved": decision.approved,
        }

    def _write_to_file(self, entry: dict[str, Any]) -> None:
        try:
            with open(self.log_file, "a", encoding="utf-8") as fh:  # type: ignore[arg-type]
                fh.write(json.dumps(entry) + "\n")
        except OSError as exc:
            logger.warning("AuditLogger: could not write to %s: %s", self.log_file, exc)
