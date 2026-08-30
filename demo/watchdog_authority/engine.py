"""Ordered, bounded recovery policy over synthetic health observations."""

from datetime import timedelta

from .model import (
    ActionKind,
    AuthorityTier,
    IssueKind,
    NotificationState,
    RecoveryDecision,
    WatchdogContext,
)


NOTIFICATION_COOLDOWN = timedelta(minutes=15)


def _decision(
    context: WatchdogContext,
    action: ActionKind,
    authority: AuthorityTier,
    healthy: bool,
    reason: str,
    records_notification: bool = False,
) -> RecoveryDecision:
    if records_notification:
        next_notification = NotificationState(
            context.now,
            context.notification.sent_count + 1,
        )
    else:
        next_notification = context.notification
    return RecoveryDecision(
        action,
        authority,
        healthy,
        reason,
        next_notification,
    )


def _inside_cooldown(context: WatchdogContext) -> bool:
    last_sent_at = context.notification.last_sent_at
    if last_sent_at is None:
        return False
    return context.now - last_sent_at < NOTIFICATION_COOLDOWN


def evaluate_issue(context: WatchdogContext) -> RecoveryDecision:
    """Choose the least-authoritative safe action for one synthetic issue."""

    if not context.external_heartbeat_present:
        return _decision(
            context,
            ActionKind.NOTIFY_HUMAN,
            AuthorityTier.HUMAN_REQUIRED,
            False,
            "missing external heartbeat cannot prove the watchdog domain is alive",
            records_notification=True,
        )

    issue = context.issue
    if issue is None:
        return _decision(
            context,
            ActionKind.NOOP,
            AuthorityTier.AUTO_FIX,
            True,
            "external heartbeat is present and no issue is observed",
        )

    if issue.kind in {IssueKind.CORRUPT_STATE, IssueKind.UNKNOWN}:
        return _decision(
            context,
            ActionKind.NOTIFY_HUMAN,
            AuthorityTier.HUMAN_REQUIRED,
            False,
            "corrupt or unknown state is outside automated recovery authority",
            records_notification=True,
        )

    if issue.kind is IssueKind.SERVICE_DOWN and issue.consecutive_count >= 3:
        return _decision(
            context,
            ActionKind.NOTIFY_HUMAN,
            AuthorityTier.HUMAN_REQUIRED,
            False,
            "repeated service failure exhausted the allowlisted restart boundary",
            records_notification=True,
        )

    if issue.kind is IssueKind.SERVICE_DOWN and issue.consecutive_count == 1:
        return _decision(
            context,
            ActionKind.RESTART_ALLOWLISTED_SERVICE,
            AuthorityTier.AUTO_FIX,
            False,
            "one bounded restart is allowed for an allowlisted service",
        )

    if issue.kind is IssueKind.STALE_TRIGGER:
        return _decision(
            context,
            ActionKind.REBUILD_EPHEMERAL_TRIGGER,
            AuthorityTier.AUTO_FIX,
            False,
            "ephemeral trigger state may be rebuilt without durable mutation",
        )

    if _inside_cooldown(context):
        return _decision(
            context,
            ActionKind.SUPPRESS_DUPLICATE,
            AuthorityTier.AGENT_REVIEW,
            False,
            "an equivalent notification was already sent inside the cooldown",
        )

    return _decision(
        context,
        ActionKind.NOTIFY_AGENT,
        AuthorityTier.AGENT_REVIEW,
        False,
        "unresolved service or pipeline state requires agent review before intervention",
        records_notification=True,
    )
