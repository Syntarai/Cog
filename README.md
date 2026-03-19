# COG

COG is a modular decision-governance engine. It processes signals through pluggable stages — context, interpretation, reasoning, harm, and execution — producing auditable, constraint-aware decisions. Built for high-stakes environments requiring transparency and control.

> COG does not optimise decisions.
> It validates whether they should occur at all.

---

## Why COG

Most systems act on signals without context.

COG enforces a structured decision process:

```
signal → context → reasoning → harm → execution
```

This prevents:

- decisions made on incomplete information
- untraceable or unjustified outcomes
- harm caused by speed without judgement

COG ensures every decision is context-aware, auditable, and accountable before execution.

---

## Example — Decision Failure vs COG

### Scenario

A tenant misses a housing appointment.

### Without COG

**Signal received:** missed appointment

→ classified as non-engagement
→ benefit reduced or sanction applied

No context is considered.

**Reality:**
- Tenant was in hospital
- No ability to attend or notify
- Medical evidence exists

### With COG

**ContextManager** retrieves:
- hospital admission record
- prior engagement history
- vulnerability indicators

**SignalInterpreter** reclassifies:
→ not non-engagement
→ constrained non-attendance

**ReasoningBuilder** constructs chain:
- attendance was not possible
- no intent to disengage
- penalty would be disproportionate

**HarmAssessor** evaluates:
- financial harm
- housing instability risk
- vulnerability impact
→ flags HIGH RISK

**ExecutionGate:** decision blocked
→ escalation triggered for human review

**Outcome:** no automatic sanction applied. Decision is delayed pending contextual review.

---

> Standard systems act on signals.
> COG validates whether action is justified before execution.

---

## Example — Automated Decision vs COG (AI / Risk Flagging)

### Scenario

An automated system flags an individual as "high risk" based on pattern matching.

### Without COG

**Signal received:** risk score above threshold

→ individual restricted or denied access
→ decision executed automatically

No explanation or context required.

**Reality:**
- Pattern triggered by incomplete or outdated data
- No recent behavioural indicators
- No human review prior to action

### With COG

**ContextManager** retrieves:
- data recency
- source reliability
- recent behaviour
- prior decisions

**SignalInterpreter** reclassifies:
→ weak signal (low confidence, incomplete data)

**ReasoningBuilder** constructs chain:
- data is outdated
- no corroborating indicators
- threshold triggered without sufficient context

**HarmAssessor** evaluates:
- reputational harm
- access restriction impact
- false positive risk
→ flags HIGH RISK (false positive)

**ExecutionGate:** decision blocked
→ escalation to human review

**Outcome:** no automatic restriction applied. Decision requires verification before action.

---

> Standard systems execute based on thresholds.
> COG validates whether the decision is justified before execution.

---

## Example — School Exclusion

### Scenario

A child is flagged for exclusion after repeated behavioural incidents.

### Without COG

**Signal received:** behaviour threshold exceeded

→ exclusion decision triggered
→ child removed from school

No underlying context reviewed.

**Reality:**
- Child has an undiagnosed SEN condition
- Behaviour linked to stress at home
- No prior assessment or support plan in place

**Consequence:** exclusion at this stage correlates with long-term educational disengagement. The decision takes seconds. The damage takes years.

### With COG

**ContextManager** retrieves:
- SEN assessment history (incomplete)
- attendance and behaviour trend
- home circumstance indicators
- prior interventions (none recorded)

**SignalInterpreter** reclassifies:
→ distress signal, not conduct failure
→ support need, not disciplinary case

**ReasoningBuilder** constructs chain:
- no prior support was offered
- behaviour is consistent with unmet need
- exclusion without assessment breaches duty of care

**HarmAssessor** evaluates:
- educational continuity risk
- long-term disengagement probability
- safeguarding exposure
→ flags CRITICAL RISK

**ExecutionGate:** decision blocked
→ mandatory assessment required before any exclusion can proceed

**Outcome:** no exclusion applied. Child referred for SEN assessment and pastoral support.

---

> The system was about to permanently alter a child's trajectory based on a behaviour count.
> COG required justification first.

---

## Pattern

Across domains, decision failure follows the same structure:

- signals interpreted without context
- thresholds applied without reasoning
- actions executed without accountability

COG intervenes at the same point each time: before execution.

---

## Case Application — Housing Decision (Islington)

This is not a hypothetical.

### Decision

Property deemed suitable for occupation despite ongoing works.

### Signals used

- repairs logged
- timeline scheduled
- "not uninhabitable" threshold applied

### Missing context

- works begin before move date
- plaster drying time required
- bedrooms and bathroom not usable at point of move-in
- no void inspection report obtained

### COG Processing

**ContextManager** retrieves:
- timeline conflict between works and tenancy start
- absence of void inspection
- functional usability status of each room

**SignalInterpreter** reclassifies:
→ not "habitable"
→ "operationally unready"

**ReasoningBuilder** constructs chain:
- works overlap with move-in date
- essential rooms unusable
- decision made without completed assessment

**HarmAssessor** evaluates:
- unusable living conditions at point of occupation
- financial and logistical burden on tenant
- child impact (bedroom not ready)
→ flags HIGH RISK

**ExecutionGate:** decision blocked
→ escalation required before tenancy can proceed

### COG verdict

Decision cannot execute without:
- confirmed works completion before move-in
- verified room usability
- or explicit, documented risk acknowledgement

### Key failure

The decision was made on repair status.

It should have been made on functional usability at point of move-in.

> These are not the same thing. The council treated them as if they were.

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
