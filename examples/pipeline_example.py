"""
Multi-stage COG pipeline example.

Demonstrates:
- Composing multiple COGs into a sequential governance pipeline
- Early termination on block verdict
- Per-stage specialisation (intake, compliance, audit)
"""

from cog import CogVerse, Signal, RiskLevel, Verdict
from cog.core.context import ContextManager


def make_signal(type_: str, source: str, priority: str = "normal", **payload) -> Signal:
    return Signal(type=type_, payload=payload, source=source, priority=priority)


def build_verse() -> CogVerse:
    verse = CogVerse(default_environment="production")

    # --- Intake COG: lightweight triage ---
    intake = verse.add_cog("intake", environment="edge")
    intake.context_manager.add_state_provider(
        lambda s: {"trusted_sources": ["api-gateway", "internal-scheduler"]}
    )

    @intake.interpreter.global_handler
    def classify_payload(signal, context, interpreted):
        if isinstance(signal.payload, dict) and signal.payload.get("bulk"):
            interpreted.annotate("bulk_operation", True)

    # --- Compliance COG: policy enforcement ---
    compliance = verse.add_cog("compliance", environment="production")
    compliance.context_manager.add_constraint_provider(
        lambda s: ["no-signal-type:schema-drop", "no-signal-type:user-purge"]
    )

    @compliance.assessor.rule
    def block_bulk_in_prod(interpreted, context, chain, assessment):
        if interpreted.annotations.get("bulk_operation") and context.environment == "production":
            assessment.identified_risks.append(
                "Bulk operations are not permitted in the production environment."
            )
            assessment.risk_level = RiskLevel.CRITICAL

    # --- Audit COG: final logging gate ---
    audit = verse.add_cog("audit", environment="production")

    @audit.gate.policy
    def require_escalation_for_high_risk(interpreted, context, assessment, decision):
        if assessment.risk_level >= RiskLevel.HIGH and decision.verdict != Verdict.BLOCK:
            decision.verdict = Verdict.ESCALATE

    return verse


def main():
    verse = build_verse()
    pipeline = verse.build_pipeline("main", ["intake", "compliance", "audit"])

    signals = [
        make_signal("read", "api-gateway", resource="reports/q1"),
        make_signal("write", "api-gateway", resource="user/42/prefs", priority="normal"),
        make_signal("write", "api-gateway", bulk=True, resource="users/*", priority="high"),
        make_signal("schema-drop", "unknown-client", table="sessions"),
    ]

    print("=== COG Pipeline: main ===\n")
    for sig in signals:
        decision = pipeline.run(sig)
        verdict = decision.verdict.value.upper()
        risk = decision.assessment.risk_level.value
        stopped_at = decision.cog_name
        print(f"[{verdict:<8}] risk={risk:<8} stage={stopped_at:<10} | {sig.type} from {sig.source}")
        if decision.assessment.identified_risks:
            for r in decision.assessment.identified_risks:
                print(f"           ↳ {r}")
    print()

    # Aggregate audit across all stages
    for stage_name in verse.cog_names():
        cog = verse.get_cog(stage_name)
        if cog.audit_logger.records:
            print(f"Audit — {stage_name}: {len(cog.audit_logger.records)} record(s)")


if __name__ == "__main__":
    main()
