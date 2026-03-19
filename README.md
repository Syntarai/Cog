# COG

COG is a modular decision-governance engine. It processes signals through pluggable stages — context, interpretation, reasoning, harm, and execution — producing auditable, constraint-aware decisions. Built for high-stakes environments requiring transparency and control.

---

## Status

COG is an active system under development.

This repository presents the structural architecture and selected components of the system.

Core decision logic, weighting models, and enforcement mechanisms are not publicly disclosed.

---

## Core Pipeline

COG operates as a modular decision pipeline composed of five replaceable stages, each fully pluggable via dependency injection:

- **ContextManager** — restores situational awareness (state, constraints, stakeholders)
- **SignalInterpreter** — annotates signals with intent (type-specific and global handlers)
- **ReasoningBuilder** — constructs auditable, step-by-step reasoning chains
- **HarmAssessor** — plugin-based evaluation framework (rules registered externally, not included in this repository)
- **ExecutionGate** — enforces policy via block/escalate callbacks and control hooks

```
Signal ──► ContextManager ──► SignalInterpreter ──► ReasoningBuilder ──► HarmAssessor ──► ExecutionGate ──► Decision
```

---

## Verse Layer

- **CogRegistry / CogComposer / CogPipeline** — orchestrate multi-stage governance pipelines with early termination on BLOCK or ESCALATE
- **CogVerse** — single top-level system entry point

---

## Supporting Components

- **AuditLogger** — append-only logging with JSONL persistence
- Structured exceptions for control flow and traceability
- Test coverage: 66 passing tests
- Includes example implementations

---

## Data Models

| Model | Purpose |
|---|---|
| `Signal` | An incoming action request, command, or event |
| `Context` | Restored situational picture (state, history, constraints) |
| `ReasoningChain` | Ordered, auditable steps leading to a conclusion |
| `HarmAssessment` | Risk level, identified risks, mitigations, verdict |
| `Decision` | Final governance outcome — fully auditable |

---

## Verdicts

| Verdict | Meaning |
|---|---|
| `PROCEED` | Safe to execute |
| `CAUTION` | Execute with additional logging or approval |
| `ESCALATE` | Hand off to a human or higher authority |
| `BLOCK` | Refuse execution entirely |

---

## Quick Start

```python
from cog import CogVerse, Signal, RiskLevel

verse = CogVerse(default_environment="production")
cog = verse.add_cog("main")

# Register a harm rule
@cog.assessor.rule
def flag_destructive(interpreted, context, chain, assessment):
    if interpreted.annotations.get("destructive"):
        assessment.identified_risks.append("Destructive operation detected.")
        assessment.risk_level = RiskLevel.HIGH

# Annotate signal types
@cog.interpreter.handler("delete")
def handle_delete(signal, context, interpreted):
    interpreted.intent = "Delete resource"
    interpreted.annotate("destructive", True)

# Process a signal
signal = Signal(type="delete", payload={"resource": "user/42"}, source="admin-ui")
decision = verse.process(signal)

print(decision.summary())
# verdict: ESCALATE  risk: high
```

### Multi-Stage Pipeline

```python
verse = CogVerse()
verse.add_cog("intake")
verse.add_cog("compliance")
verse.add_cog("audit")

pipeline = verse.build_pipeline("main", ["intake", "compliance", "audit"])
decision = pipeline.run(signal)
```

The pipeline halts early if any stage produces a `BLOCK` or `ESCALATE` verdict — the strictest governance wins.

---

## Audit Trail

Every Decision is recorded in an append-only `AuditLogger`:

```python
for record in cog.audit_logger.records:
    print(record["verdict"], record["risk_level"], record["signal_type"])
```

Optionally persist to a JSONL file:

```python
from cog.utils.audit import AuditLogger
audit = AuditLogger(cog_name="main", log_file="/var/log/cog.jsonl")
```

---

## Project Structure

```
cog/
├── core/
│   ├── context.py      # ContextManager
│   ├── signal.py       # SignalInterpreter
│   ├── reasoning.py    # ReasoningBuilder
│   ├── harm.py         # HarmAssessor (plugin framework)
│   ├── gate.py         # ExecutionGate
│   └── engine.py       # CogEngine — pipeline orchestrator
├── verse/
│   ├── registry.py     # CogRegistry
│   ├── composer.py     # CogComposer / CogPipeline
│   └── verse.py        # CogVerse — top-level entry point
├── models/
│   ├── signal.py
│   ├── context.py
│   ├── assessment.py   # RiskLevel, Verdict, HarmAssessment
│   └── decision.py     # ReasoningStep, ReasoningChain, Decision
└── utils/
    └── audit.py        # AuditLogger
examples/
├── basic_usage.py
└── pipeline_example.py
tests/
```
