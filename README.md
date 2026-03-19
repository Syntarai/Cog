# COG

COG is a decision-governance layer that restores context before action. It forces systems to interpret signals, expose reasoning, and assess harm before execution, preventing uncontextualised and unsafe decisions in high-stakes environments.

---

## Status

COG is an active system under development.

This repository presents the structural architecture and selected components of the system.

Core decision logic, weighting models, and enforcement mechanisms are not publicly disclosed.

---

## The Verse System

The **COG Verse** is the runtime universe in which one or more COG governance units operate. Each unit (a *cog*) runs an independent, fully auditable governance pipeline. Cogs are registered in a central **Verse**, composed into multi-stage **Pipelines**, and invoked per signal.

```
Signal ──► ContextManager ──► SignalInterpreter ──► ReasoningBuilder ──► HarmAssessor ──► ExecutionGate ──► Decision
```

Every stage is replaceable. Teams plug in domain-specific implementations for any component while inheriting the governance structure.

---

## Architecture

### Core Pipeline Stages

| Stage | Component | Responsibility |
|---|---|---|
| 1 | `ContextManager` | Restores situational awareness before acting |
| 2 | `SignalInterpreter` | Derives intent and enriches the signal with annotations |
| 3 | `ReasoningBuilder` | Constructs an auditable chain of reasoning steps |
| 4 | `HarmAssessor` | Evaluates risk and recommends a verdict (rules not disclosed) |
| 5 | `ExecutionGate` | Applies final policies and emits the Decision |

### Data Models

| Model | Purpose |
|---|---|
| `Signal` | An incoming action request, command, or event |
| `Context` | Restored situational picture (state, history, constraints) |
| `ReasoningChain` | Ordered, auditable steps leading to a conclusion |
| `HarmAssessment` | Risk level, identified risks, mitigations, verdict |
| `Decision` | Final governance outcome — fully auditable |

### Verse Components

| Component | Purpose |
|---|---|
| `CogVerse` | Top-level entry point; manages the cog registry |
| `CogRegistry` | Named store of CogEngine instances |
| `CogComposer` | Assembles cogs into ordered pipelines |
| `CogPipeline` | Executes a multi-stage governance sequence |

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

## Verdicts

| Verdict | Meaning |
|---|---|
| `PROCEED` | Safe to execute |
| `CAUTION` | Execute with additional logging or approval |
| `ESCALATE` | Hand off to a human or higher authority |
| `BLOCK` | Refuse execution entirely |

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
