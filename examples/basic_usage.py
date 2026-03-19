"""
Basic COG Verse usage example.

Demonstrates:
- Creating a CogVerse and registering a COG
- Defining a custom harm rule
- Processing a signal and inspecting the Decision
"""

from cog import CogVerse, Signal, RiskLevel


def main():
    # 1. Create the verse
    verse = CogVerse(default_environment="production")

    # 2. Register a COG with a custom context and harm rules
    cog = verse.add_cog(
        "operations",
        environment="production",
    )

    # 3. Teach the context manager about trusted sources
    cog.context_manager.add_state_provider(
        lambda sig: {"trusted_sources": ["orchestrator", "scheduler"]}
    )

    # 4. Enforce a production constraint
    cog.context_manager.add_constraint_provider(
        lambda sig: ["no-signal-type:destructive-wipe"]
    )

    # 5. Register a harm rule: flag high-priority signals in production
    @cog.assessor.rule
    def flag_high_priority(interpreted, context, chain, assessment):
        if interpreted.signal.priority == "high" and context.environment == "production":
            assessment.identified_risks.append(
                "High-priority signal requires elevated scrutiny in production."
            )
            if assessment.risk_level < RiskLevel.MEDIUM:
                assessment.risk_level = RiskLevel.MEDIUM

    # 6. Interpret signal type for audit clarity
    @cog.interpreter.handler("write")
    def interpret_write(signal, context, interpreted):
        interpreted.intent = f"Write operation on resource: {signal.payload.get('resource', 'unknown')}"
        interpreted.annotate("mutating", True)

    # 7. Process a routine signal
    routine = Signal(
        type="read",
        payload={"resource": "metrics/cpu"},
        source="orchestrator",
        priority="normal",
    )

    decision = verse.process(routine, cog_name="operations")
    print("=== Routine Signal ===")
    print(decision.summary())
    print()

    # 8. Process a high-priority write signal
    urgent = Signal(
        type="write",
        payload={"resource": "config/limits", "value": 500},
        source="orchestrator",
        priority="high",
    )

    decision = verse.process(urgent, cog_name="operations")
    print("=== Urgent Write Signal ===")
    print(decision.summary())
    print()

    # 9. Show audit trail
    print(f"Audit records: {len(cog.audit_logger.records)}")
    for rec in cog.audit_logger.records:
        print(f"  [{rec['verdict'].upper()}] {rec['signal_type']} from {rec['signal_source']}")


if __name__ == "__main__":
    main()
