[繁體中文](when-agent-and-exchange-disagree.zh-TW.md)

# When the Agent and the Exchange Disagree

## Incident reconstruction

### Before

The local ledger and exchange both reported one system-owned open position with the same lifecycle.

### Failure

A partial close left the local ledger `closed` and the exchange position `open`. The agent could no longer
infer external exposure from its own state.

### Decision

Preserve both observations, classify `exit_not_committed`, resolve ownership, and apply kill-switch
precedence before authorizing any mutation. Never rewrite either record to manufacture agreement.

### Permanent fix

Allow at most one bounded retry for a confirmed transient failure, re-observe both authorities, and send
every unresolved or ambiguous state across the human boundary with typed evidence.

![Local and exchange state split after a partial commit](../assets/failure-timeline.svg)

## The problem

External execution and local state do not commit atomically. A close request may reach the external venue
while a local write fails; a local record may close while the external position remains open; or a human
may create a position the agent never owned. Treating every mismatch as “sync and continue” can duplicate
exposure or mutate the wrong position.

The difficult question is not which copy is universally correct. It is which observation is authoritative
for the next specific action—and whether the system owns the state it is about to change.

![A reconciliation state machine](../assets/reconciliation-state-machine.svg)

## The decision

ORINX separated observation, classification, authorization, and mutation:

1. Preserve external and local observations independently.
2. Classify the disagreement before proposing a repair.
3. Resolve ownership before any external mutation.
4. Apply kill-switch precedence.
5. Choose the least-authoritative action that remains safe.
6. Escalate ambiguity instead of manufacturing certainty.

The clean-room engine returns a typed finding and typed action rather than performing a side effect. A
second guard rejects any automatic account／database mutation, any exchange mutation under the kill
switch, and any exchange mutation involving manual or unknown ownership.

## Five failure classes

### Exchange-only

The external observation contains a position that is absent from the local ledger.

- **Manual ownership:** leave untouched.
- **Unknown ownership:** alert a human; never infer ownership from absence.
- **System ownership:** treat as an orphan incident and request explicit review.

Evidence: [`test_manual_exchange_position_is_never_mutated`](../tests/test_reconciliation.py) and
[`test_unknown_exchange_owner_fails_closed_to_human`](../tests/test_reconciliation.py).

### Local-only

The local ledger contains an open record absent from external observations. Local settlement is allowed
only when a separate, verified synthetic close record matches the same position lifecycle and belongs to
the current observation window. Stale, future, prior-lifecycle, or missing evidence escalates.

Evidence: [`test_verified_local_only_position_can_settle_local_ledger`](../tests/test_reconciliation.py),
[`test_stale_close_evidence_cannot_settle_a_reopened_local_position`](../tests/test_reconciliation.py), and
[`test_close_evidence_from_a_prior_position_lifecycle_is_rejected`](../tests/test_reconciliation.py).

### Direction mismatch

The two systems refer to the same instrument but disagree on side. The demo classifies this before matching
by the complete position key, so it cannot accidentally convert one contradiction into two unrelated
missing records. No automatic repair is allowed.

Evidence: [`test_direction_mismatch_never_autofixes`](../tests/test_reconciliation.py).

### Lifecycle mismatch

Matching instrument, side, quantity, and status still do not prove that two observations describe the same
position instance. If the lifecycle identities differ, the engine emits a critical typed finding and requires
human review instead of returning `aligned`.

Evidence: [`test_different_position_lifecycles_never_report_aligned`](../tests/test_reconciliation.py).

### Incomplete exit

The local record is closed but external state remains open. One retry is allowed only for a system-owned
position, only after a recorded transient failure, and only while the kill switch is off. Any other shape
escalates.

Evidence: [`test_transient_system_exit_failure_retries_once_when_enabled`](../tests/test_reconciliation.py)
and [`test_kill_switch_blocks_retry_exchange_close`](../tests/test_reconciliation.py).

### Guard states: status mismatch and ambiguous observations

The engine also refuses to label opposite open／closed status as aligned, and it does not mislabel multiple
observations as a quantity error. Both states receive their own finding and require human review.

Evidence: [`test_closed_exchange_and_open_local_is_state_mismatch`](../tests/test_reconciliation.py) and
[`test_duplicate_observations_are_ambiguous_not_quantity_mismatch`](../tests/test_reconciliation.py).

## Why mutation order matters

The engine deliberately distinguishes “observe a mismatch” from “repair a mismatch.” An external action
cannot be made safe merely by updating the local ledger first, and a local settlement cannot be justified
merely because an external position is absent. Each mutation needs its own evidence and authority.

## Trade-off

Failing closed leaves some incidents unresolved longer and increases human review. That is an explicit
availability cost. The alternative—automatically closing a manual position, retrying through a kill
switch, or marking local state closed without evidence—creates a larger and less reversible failure.

## Inspect it offline

```bash
python3 -m unittest tests.test_reconciliation -v
python3 -m demo.reconciliation.example
```

The failure classes were derived from operating experience, but this public case contains only synthetic
instruments, quantities, timestamps, and evidence.
