"""Typed inputs and outputs for the synthetic reconciliation demo."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PositionSide(StrEnum):
    LONG = "long"
    SHORT = "short"


class PositionStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class OwnerTag(StrEnum):
    SYSTEM = "system"
    MANUAL = "manual"
    UNKNOWN = "unknown"


class FindingKind(StrEnum):
    ALIGNED = "aligned"
    EXCHANGE_ONLY = "exchange_only"
    LOCAL_ONLY = "local_only"
    DIRECTION_MISMATCH = "direction_mismatch"
    LIFECYCLE_MISMATCH = "lifecycle_mismatch"
    QUANTITY_MISMATCH = "quantity_mismatch"
    STATE_MISMATCH = "state_mismatch"
    AMBIGUOUS_OBSERVATION = "ambiguous_observation"
    EXIT_NOT_COMMITTED = "exit_not_committed"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ActionKind(StrEnum):
    NOOP = "noop"
    LEAVE_UNTOUCHED = "leave_untouched"
    SETTLE_LOCAL = "settle_local"
    RETRY_EXCHANGE_CLOSE = "retry_exchange_close"
    ALERT_HUMAN = "alert_human"


class AuthorityTier(StrEnum):
    AUTO_FIX = "auto_fix"
    AGENT_REVIEW = "agent_review"
    HUMAN_REQUIRED = "human_required"


class MutationTarget(StrEnum):
    NONE = "none"
    LOCAL_LEDGER = "local_ledger"
    EXCHANGE = "exchange"
    ACCOUNT = "account"
    DATABASE = "database"


@dataclass(frozen=True, order=True)
class PositionKey:
    instrument: str
    side: PositionSide
    lifecycle_id: str = "SYNTH-LIFE-DEFAULT"

    def __post_init__(self) -> None:
        if not self.instrument.startswith("SYNTH-") or len(self.instrument) == 6:
            raise ValueError("a synthetic instrument must use a non-empty SYNTH-* name")
        if not self.lifecycle_id.startswith("SYNTH-LIFE-") or len(self.lifecycle_id) == 11:
            raise ValueError("a position lifecycle must use a non-empty SYNTH-LIFE-* id")


@dataclass(frozen=True)
class ExchangePosition:
    key: PositionKey
    quantity: int
    owner_tag: OwnerTag
    status: PositionStatus

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("exchange position quantity must be positive")


@dataclass(frozen=True)
class LocalPosition:
    key: PositionKey
    status: PositionStatus
    expected_quantity: int

    def __post_init__(self) -> None:
        if self.expected_quantity <= 0:
            raise ValueError("local position quantity must be positive")


@dataclass(frozen=True)
class CloseEvidence:
    key: PositionKey
    verified: bool
    closed_at: datetime


@dataclass(frozen=True)
class ReconciliationFinding:
    kind: FindingKind
    severity: Severity
    key: PositionKey
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class RecoveryAction:
    kind: ActionKind
    authority: AuthorityTier
    mutation_target: MutationTarget
    reason: str


@dataclass(frozen=True)
class ReconciliationDecision:
    finding: ReconciliationFinding
    actions: tuple[RecoveryAction, ...]


@dataclass(frozen=True)
class ReconciliationContext:
    exchange_positions: tuple[ExchangePosition, ...]
    local_positions: tuple[LocalPosition, ...]
    close_evidence: tuple[CloseEvidence, ...]
    transient_exit_failures: tuple[tuple[PositionKey, int], ...]
    kill_switch_active: bool
    observed_at: datetime
