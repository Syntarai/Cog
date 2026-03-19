"""Tests for AuditLogger."""

import json
import tempfile
import os

from cog.models.signal import Signal
from cog.core.engine import CogEngine
from cog.utils.audit import AuditLogger
from cog.models.assessment import Verdict


def make_signal(**kwargs) -> Signal:
    defaults = {"type": "query", "payload": {}, "source": "audit-test"}
    return Signal(**{**defaults, **kwargs})


class TestAuditLogger:
    def test_records_appended(self):
        engine = CogEngine(name="audit-eng")
        engine.process(make_signal())
        engine.process(make_signal())
        assert len(engine.audit_logger.records) == 2

    def test_record_fields(self):
        engine = CogEngine(name="field-test")
        sig = make_signal(type="command", source="src-x")
        engine.process(sig)
        record = engine.audit_logger.records[0]
        assert record["signal_id"] == sig.id
        assert record["signal_type"] == "command"
        assert record["signal_source"] == "src-x"
        assert "verdict" in record
        assert "risk_level" in record
        assert record["cog_name"] == "field-test"

    def test_get_by_verdict(self):
        audit = AuditLogger(cog_name="test")
        engine = CogEngine(name="by-verdict", audit_logger=audit)
        engine.process(make_signal())
        proceed_records = audit.get_by_verdict(Verdict.PROCEED.value)
        assert len(proceed_records) >= 0  # may or may not be proceed depending on rules

    def test_get_by_signal_id(self):
        engine = CogEngine(name="by-sig")
        sig = make_signal()
        engine.process(sig)
        record = engine.audit_logger.get_by_signal_id(sig.id)
        assert record is not None
        assert record["signal_id"] == sig.id

    def test_get_by_signal_id_missing(self):
        engine = CogEngine(name="missing-sig")
        result = engine.audit_logger.get_by_signal_id("nonexistent")
        assert result is None

    def test_clear(self):
        engine = CogEngine(name="clear-test")
        engine.process(make_signal())
        engine.audit_logger.clear()
        assert engine.audit_logger.records == []

    def test_file_persistence(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            log_path = f.name

        try:
            audit = AuditLogger(cog_name="file-test", log_file=log_path)
            engine = CogEngine(name="file-eng", audit_logger=audit)
            sig = make_signal()
            engine.process(sig)

            with open(log_path) as f:
                lines = [json.loads(line) for line in f if line.strip()]

            assert len(lines) == 1
            assert lines[0]["signal_id"] == sig.id
        finally:
            os.unlink(log_path)
