[繁體中文](architecture.zh-TW.md)

# Architecture and evidence map

ORINX separated probabilistic decisions from deterministic authority. The AI-facing layer could choose
entry, skip, exit, or hold; it did not receive unlimited execution or recovery rights.

![ORINX bounded agent-operations architecture](../assets/architecture.svg)

## Responsibility chain

```text
Synthetic market/signal input
    -> AI entry/skip/exit/hold decision
    -> deterministic safety gate
    -> bounded executor
    -> external execution state + local decision ledger
    -> reconciliation
    -> watchdog / tiered recovery
    -> agent review or human escalation
```

The external execution node is an architectural boundary, not a connection in this repository. The public
demo has no client, endpoint, environment configuration, deployment command, or credential input.

## Node-to-evidence map

| Node | Responsibility | Public evidence | Review route |
|---|---|---|---|
| Synthetic input | Provide fixed observations without live data | Both example modules | `ORX-DEMO-01`, `ORX-DEMO-02` |
| AI decision | Express entry／skip／exit／hold intent | Architecture narrative only | `ORX-ARCH-01` |
| Safety gate | Apply kill-switch precedence before an exchange mutation | [`test_kill_switch_blocks_retry_exchange_close`](../tests/test_reconciliation.py) | `ORX-CASE-01` |
| Bounded executor | Permit only a typed action and mutation target | [`RecoveryAction`](../demo/reconciliation/model.py) | `ORX-DEMO-01` |
| External state + local ledger | Keep two observations distinct until reconciled | [`ReconciliationContext`](../demo/reconciliation/model.py) | `ORX-CASE-01` |
| Reconciliation | Classify drift and choose the least-authoritative safe action | [`reconcile`](../demo/reconciliation/engine.py) | `ORX-DEMO-01` |
| Watchdog | Evaluate health issues without accepting arbitrary commands | [`evaluate_issue`](../demo/watchdog_authority/engine.py) | `ORX-DEMO-02` |
| Escalation | Route ambiguity, durable mutation, or missing external evidence upward | Both behavioral test suites | `ORX-CASE-02` |

Review-route identifiers are stable internal evidence labels. They do not link to the private product tree.

## State and authority are separate types

The reconciliation demo does not return a boolean “synced” value. It returns:

- a `FindingKind` describing what disagrees;
- a `Severity` describing operational risk;
- evidence explaining the observation;
- an `ActionKind`;
- an `AuthorityTier`; and
- a `MutationTarget`.

This shape makes an unsafe shortcut visible. For example, a proposed exchange mutation can be rejected if
the kill switch is active or ownership is manual／unknown, even if the classification logic requested it.

The watchdog demo applies the same principle to recovery. It evaluates a synthetic issue against a policy
table; it never accepts a shell command, process path, database handle, or callable repair action.

## Failure-domain boundary

An internal watchdog can observe application state but cannot prove that its own scheduling domain is
alive. The public policy therefore treats missing external-heartbeat evidence as an unhealthy state that
requires human escalation. This is a deliberate refusal to turn absence of evidence into evidence of
health.

