"""Deterministic CLI examples for the recovery-authority case."""

from datetime import UTC, datetime, timedelta
import json

from .engine import evaluate_issue
from .model import IssueKind, NotificationState, WatchdogContext, WatchdogIssue


OBSERVED_AT = datetime(2026, 1, 15, 12, tzinfo=UTC)


def _serialize(scenario: str, context: WatchdogContext) -> dict[str, str | bool]:
    decision = evaluate_issue(context)
    return {
        "action": decision.action.value,
        "authority": decision.authority.value,
        "healthy": decision.healthy,
        "scenario": scenario,
    }


def build_examples() -> tuple[dict[str, str | bool], ...]:
    """Return four fixed scenarios spanning the recovery authority boundary."""

    return (
        _serialize(
            "allowlisted_restart",
            WatchdogContext(
                issue=WatchdogIssue(IssueKind.SERVICE_DOWN, 1, OBSERVED_AT),
                notification=NotificationState(None, 0),
                external_heartbeat_present=True,
                now=OBSERVED_AT,
            ),
        ),
        _serialize(
            "corrupt_state",
            WatchdogContext(
                issue=WatchdogIssue(IssueKind.CORRUPT_STATE, 1, OBSERVED_AT),
                notification=NotificationState(None, 0),
                external_heartbeat_present=True,
                now=OBSERVED_AT,
            ),
        ),
        _serialize(
            "notification_cooldown",
            WatchdogContext(
                issue=WatchdogIssue(IssueKind.STALE_PIPELINE, 1, OBSERVED_AT),
                notification=NotificationState(
                    OBSERVED_AT - timedelta(minutes=5),
                    1,
                ),
                external_heartbeat_present=True,
                now=OBSERVED_AT,
            ),
        ),
        _serialize(
            "missing_external_heartbeat",
            WatchdogContext(
                issue=None,
                notification=NotificationState(None, 0),
                external_heartbeat_present=False,
                now=OBSERVED_AT,
            ),
        ),
    )


def render_examples() -> str:
    """Serialize the fixed scenarios as stable, human-readable JSON."""

    return json.dumps(build_examples(), ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    print(render_examples())
