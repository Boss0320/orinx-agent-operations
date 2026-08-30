[繁體中文](evolution.zh-TW.md)

# Evolution: from persistent agent to bounded operations

ORINX did not begin as a finished operating system. Its public value is the sequence of problems that
changed the success criterion—from making an AI trading judgment to governing a long-running agent that
could affect an external system.

The stages below describe one project lineage. They do not imply that every module existed from the first
day, that each stage was equally mature, or that the original product is currently connected to a live
venue.

## 1. February 2026 — persistent trading assistant

**Problem.** A one-off model answer was insufficient for a workflow that needed memory, repeated signal
review, and explicit entry／skip／exit／hold decisions.

**Capability.** The first ORINX system established persistent decision routing and a durable project
identity around an AI-assisted trading workflow.

**Limitation.** Producing a decision was easier than proving that scheduling, execution, and state would
remain coherent over time.

**Evidence route.** `ORX-EVOL-01` — root project history and frozen architecture evidence.

## 2. March–April 2026 — long-running operating workflow

**Problem.** A persistent agent also needs scheduled observation, deterministic execution controls, local
records, and health monitoring.

**Capability.** The system expanded into a scheduled workflow with a signal gate, bounded executor,
external execution boundary, local state, reconciliation, and watchdog roles.

**Limitation.** More automation created more partial-failure surfaces. A task could succeed externally and
fail locally, or a monitor could share the same failure domain as the scheduler it was meant to watch.

**Evidence route.** `ORX-ARCH-01` — frozen production-caller and scheduling evidence.

## 3. April–May 2026 — failure-driven hardening

**Problem.** Real operations exposed disagreement between external and local state, orphaned exits,
ownership ambiguity, silent scheduling failure, and cross-strategy contamination.

**Capability.** Kill-switch precedence, explicit position ownership, typed reconciliation states, bounded
retry, notification deduplication, and incident records became first-class mechanisms.

**Limitation.** Detecting a problem still did not answer who was allowed to repair it.

**Evidence route.** `ORX-CASE-01` and `ORX-CASE-02` — sanitized failure classes; no original incident bytes
are part of this repository.

## 4. May 2026 — bounded governance

**Problem.** A long-running agent can make an incident worse if detection automatically grants mutation
authority.

**Capability.** Recovery became tiered: ephemeral allowlisted repair, bounded retry, agent review, or human
escalation. Unknown ownership and durable high-risk state fail closed.

**Limitation.** Operational safety does not establish trading quality. A convincing backtest can still be
wrong because of point-in-time, cost, ledger, or trial-count errors.

**Evidence route.** `ORX-DEMO-01` and `ORX-DEMO-02` — the clean-room state machines and their tests.

## 5. Later audit work — evidence-first evaluation

**Problem.** Strategy evaluation needs a canonical decision ledger, point-in-time inputs, cost and funding
treatment, and reproducible trial accounting.

**Capability.** A separate forensic-audit effort defined those contracts and built a larger test surface.

**Current boundary.** That audit is non-terminal and is not shipped here as evidence of trading quality.
This repository includes only the two operating-control cases that can already be supported and inspected.

**Evidence route.** `ORX-AUDIT-01` — blocked from public completion claims until a committed, independently
reviewed terminal state exists.

## What changed

The durable lesson was not “add more automation.” It was to make every side effect answer three questions:

1. Which observation is authoritative for this decision?
2. Who owns the state being changed?
3. What is the least-authoritative action that remains safe?

That is the design contract implemented in the two public demos.

