"""Typed policy inputs and decisions for the watchdog authority demo."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class IssueKind(StrEnum):
    STALE_PIPELINE = "stale_pipeline"
    STALE_TRIGGER = "stale_trigger"
    CORRUPT_STATE = "corrupt_state"
    SERVICE_DOWN = "service_down"
    UNKNOWN = "unknown"


class ActionKind(StrEnum):
    NOOP = "noop"
    REBUILD_EPHEMERAL_TRIGGER = "rebuild_ephemeral_trigger"
    RESTART_ALLOWLISTED_SERVICE = "restart_allowlisted_service"
    NOTIFY_AGENT = "notify_agent"
    NOTIFY_HUMAN = "notify_human"
    SUPPRESS_DUPLICATE = "suppress_duplicate"


class AuthorityTier(StrEnum):
    AUTO_FIX = "auto_fix"
    AGENT_REVIEW = "agent_review"
    HUMAN_REQUIRED = "human_required"


@dataclass(frozen=True)
class WatchdogIssue:
    kind: IssueKind
    consecutive_count: int
    last_seen_at: datetime

    def __post_init__(self) -> None:
        if self.consecutive_count <= 0:
            raise ValueError("watchdog issue consecutive count must be positive")


@dataclass(frozen=True)
class NotificationState:
    last_sent_at: datetime | None
    sent_count: int

    def __post_init__(self) -> None:
        if self.sent_count < 0:
            raise ValueError("notification count cannot be negative")


@dataclass(frozen=True)
class WatchdogContext:
    issue: WatchdogIssue | None
    notification: NotificationState
    external_heartbeat_present: bool
    now: datetime


@dataclass(frozen=True)
class RecoveryDecision:
    action: ActionKind
    authority: AuthorityTier
    healthy: bool
    reason: str
    next_notification: NotificationState
