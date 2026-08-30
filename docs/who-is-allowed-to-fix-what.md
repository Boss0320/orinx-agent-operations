[繁體中文](who-is-allowed-to-fix-what.zh-TW.md)

# Who Is Allowed to Fix What?

## The problem

Detection is not authorization. A watchdog may know that a pipeline is stale or a service is down without
being qualified to rewrite durable state, restart an arbitrary process, or declare itself healthy.

ORINX moved recovery decisions into an explicit authority matrix. The public demo evaluates one synthetic
issue and returns an action, authority tier, health state, reason, and next notification state. It cannot
accept a command, path, database handle, or callable action.

## Authority matrix

| Failure class | Detected by | Allowed action | Authority | Mutation surface | Escalation |
|---|---|---|---|---|---|
| Ephemeral stale trigger | Internal watchdog | Rebuild ephemeral trigger state | Auto fix | Ephemeral local state | Agent if the issue persists |
| Allowlisted service down once | Internal watchdog | One bounded restart | Auto fix | One predefined service boundary | Human after repeated failure |
| Second consecutive service failure | Consecutive observation count | Notify agent; do not restart again | Agent review | None | Human if failure continues |
| Repeated service failure | Consecutive observation count | Notify human | Human required | None | Immediate human review |
| Stale decision pipeline | Freshness observation | Notify agent | Agent review | None | Human if unresolved |
| Corrupt state | Integrity observation | Notify human | Human required | None | Human decides any durable repair |
| Unknown issue | Unmapped observation | Notify human | Human required | None | Add a policy only after review |
| External heartbeat absent | Independent liveness evidence | Notify human and remain unhealthy | Human required | None | Inspect the shared failure domain |

This table matches [`evaluate_issue`](../demo/watchdog_authority/engine.py). It is intentionally small: the
public demo proves an authority policy, not a general remote-execution framework.

## Ordered policy

Policy order matters because a lower-risk branch must not hide a higher-risk state:

1. Missing external heartbeat always remains unhealthy and escalates to a human.
2. No issue plus present external heartbeat is the only healthy result.
3. Corrupt or unknown state always requires a human.
4. Repeated service failure exhausts bounded restart authority.
5. The first allowlisted service failure may receive one bounded restart decision.
6. Ephemeral trigger state may be rebuilt automatically.
7. Duplicate agent-level notifications are suppressed inside a fixed cooldown while health remains false;
   cooldown never suppresses the allowlisted recovery decisions above it.
8. A second consecutive service failure or stale decision pipeline routes to agent review when no equivalent
   notification is already inside the cooldown.

## Notification cooldown is not recovery

Suppressing a duplicate notification changes message volume, not system health. The returned decision
therefore keeps `healthy=False`. A cooldown can prevent alert storms without pretending the underlying
issue disappeared.

Evidence: [`test_notification_is_deduped_inside_cooldown`](../tests/test_watchdog_authority.py).

## The common-cause blind spot

If a scheduler and its watchdog share one failure domain, both can stop together. An internal “no issue”
observation cannot prove liveness when the observer may itself be absent. The policy requires independent
external-heartbeat evidence before it can return a healthy state.

Evidence: [`test_missing_external_heartbeat_never_reports_health`](../tests/test_watchdog_authority.py).

## Trade-off

The matrix intentionally automates less than a generic recovery bot. It may require a person for incidents
that could sometimes be repaired automatically. In exchange, detecting a new failure does not silently
grant the system new mutation authority.

## Inspect it offline

```bash
python3 -m unittest tests.test_watchdog_authority -v
python3 -m demo.watchdog_authority.example
```
