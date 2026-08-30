"""Deterministic, bounded reconciliation over synthetic observations."""

from collections import defaultdict
from datetime import timedelta

from .model import (
    ActionKind,
    AuthorityTier,
    ExchangePosition,
    FindingKind,
    LocalPosition,
    MutationTarget,
    OwnerTag,
    PositionKey,
    PositionStatus,
    ReconciliationContext,
    ReconciliationDecision,
    ReconciliationFinding,
    RecoveryAction,
    Severity,
)


CLOSE_EVIDENCE_VALID_FOR = timedelta(hours=1)


def _finding(
    kind: FindingKind,
    severity: Severity,
    key: PositionKey,
    *evidence: str,
) -> ReconciliationFinding:
    return ReconciliationFinding(kind, severity, key, tuple(evidence))


def _action(
    kind: ActionKind,
    authority: AuthorityTier,
    target: MutationTarget,
    reason: str,
) -> RecoveryAction:
    return RecoveryAction(kind, authority, target, reason)


def _human(reason: str) -> RecoveryAction:
    return _action(
        ActionKind.ALERT_HUMAN,
        AuthorityTier.HUMAN_REQUIRED,
        MutationTarget.NONE,
        reason,
    )


def _validate_action(
    action: RecoveryAction,
    context: ReconciliationContext,
    owner: OwnerTag | None,
) -> None:
    if action.authority is AuthorityTier.AUTO_FIX and action.mutation_target in {
        MutationTarget.ACCOUNT,
        MutationTarget.DATABASE,
    }:
        raise AssertionError("automatic recovery cannot mutate account or database state")
    if (
        context.kill_switch_active
        and action.mutation_target is MutationTarget.EXCHANGE
    ):
        raise AssertionError("kill switch blocks exchange mutation")
    if (
        action.mutation_target is MutationTarget.EXCHANGE
        and owner in {OwnerTag.MANUAL, OwnerTag.UNKNOWN}
    ):
        raise AssertionError("manual or unknown ownership blocks exchange mutation")


def _decision(
    finding: ReconciliationFinding,
    actions: tuple[RecoveryAction, ...],
    context: ReconciliationContext,
    owner: OwnerTag | None,
) -> ReconciliationDecision:
    for action in actions:
        _validate_action(action, context, owner)
    return ReconciliationDecision(finding, actions)


def _direction_mismatch(
    exchange: ExchangePosition,
    local: LocalPosition,
    context: ReconciliationContext,
) -> ReconciliationDecision:
    finding = _finding(
        FindingKind.DIRECTION_MISMATCH,
        Severity.CRITICAL,
        exchange.key,
        "exchange and local ledgers disagree on position side",
    )
    return _decision(
        finding,
        (_human("direction mismatch is an ambiguous high-risk state"),),
        context,
        exchange.owner_tag,
    )


def _exchange_only(
    exchange: ExchangePosition,
    context: ReconciliationContext,
) -> ReconciliationDecision:
    finding = _finding(
        FindingKind.EXCHANGE_ONLY,
        Severity.WARNING,
        exchange.key,
        "exchange reports a position without a local open record",
        f"owner={exchange.owner_tag.value}",
    )
    if exchange.owner_tag is OwnerTag.MANUAL:
        actions = (
            _action(
                ActionKind.LEAVE_UNTOUCHED,
                AuthorityTier.AGENT_REVIEW,
                MutationTarget.NONE,
                "manual-owned positions remain outside automated mutation authority",
            ),
        )
    elif exchange.owner_tag is OwnerTag.UNKNOWN:
        actions = (_human("unknown ownership must be resolved before any mutation"),)
    else:
        actions = (_human("system-owned orphan requires explicit incident review"),)
    return _decision(finding, actions, context, exchange.owner_tag)


def _local_only(
    local: LocalPosition,
    context: ReconciliationContext,
) -> ReconciliationDecision:
    finding = _finding(
        FindingKind.LOCAL_ONLY,
        Severity.WARNING,
        local.key,
        "local ledger reports an open position absent from exchange observations",
    )
    verified_keys = {
        evidence.key
        for evidence in context.close_evidence
        if evidence.verified
        and evidence.closed_at <= context.observed_at
        and context.observed_at - evidence.closed_at <= CLOSE_EVIDENCE_VALID_FOR
    }
    if local.status is PositionStatus.OPEN and local.key in verified_keys:
        actions = (
            _action(
                ActionKind.SETTLE_LOCAL,
                AuthorityTier.AUTO_FIX,
                MutationTarget.LOCAL_LEDGER,
                "same-lifecycle close evidence from the observation window authorizes settlement",
            ),
        )
    else:
        actions = (_human("local-only state lacks current same-lifecycle close evidence"),)
    return _decision(finding, actions, context, None)


def _paired(
    exchange: ExchangePosition,
    local: LocalPosition,
    context: ReconciliationContext,
) -> ReconciliationDecision:
    if exchange.key.lifecycle_id != local.key.lifecycle_id:
        finding = _finding(
            FindingKind.LIFECYCLE_MISMATCH,
            Severity.CRITICAL,
            exchange.key,
            "exchange and local observations refer to different position lifecycles",
        )
        return _decision(
            finding,
            (_human("lifecycle mismatch cannot be reconciled automatically"),),
            context,
            exchange.owner_tag,
        )

    if exchange.quantity != local.expected_quantity:
        finding = _finding(
            FindingKind.QUANTITY_MISMATCH,
            Severity.CRITICAL,
            exchange.key,
            "exchange and local quantities disagree",
        )
        return _decision(
            finding,
            (_human("quantity mismatch requires human ownership review"),),
            context,
            exchange.owner_tag,
        )

    if (
        exchange.status is PositionStatus.OPEN
        and local.status is PositionStatus.CLOSED
    ):
        finding = _finding(
            FindingKind.EXIT_NOT_COMMITTED,
            Severity.CRITICAL,
            exchange.key,
            "local close is not reflected in exchange state",
        )
        failure_counts = dict(context.transient_exit_failures)
        failures = failure_counts.get(exchange.key, 0)
        can_retry = (
            exchange.owner_tag is OwnerTag.SYSTEM
            and not context.kill_switch_active
            and 0 < failures < 2
        )
        if can_retry:
            actions = (
                _action(
                    ActionKind.RETRY_EXCHANGE_CLOSE,
                    AuthorityTier.AUTO_FIX,
                    MutationTarget.EXCHANGE,
                    "one bounded retry is allowed for a transient system-owned exit",
                ),
            )
        else:
            actions = (_human("exchange close cannot be retried within bounded authority"),)
        return _decision(finding, actions, context, exchange.owner_tag)

    if exchange.status is not local.status:
        finding = _finding(
            FindingKind.STATE_MISMATCH,
            Severity.CRITICAL,
            exchange.key,
            "exchange and local position status disagree",
        )
        return _decision(
            finding,
            (_human("status mismatch requires independent close evidence"),),
            context,
            exchange.owner_tag,
        )

    finding = _finding(
        FindingKind.ALIGNED,
        Severity.INFO,
        exchange.key,
        "exchange and local observations are aligned",
    )
    actions = (
        _action(
            ActionKind.NOOP,
            AuthorityTier.AUTO_FIX,
            MutationTarget.NONE,
            "no reconciliation action is required",
        ),
    )
    return _decision(finding, actions, context, exchange.owner_tag)


def reconcile(
    context: ReconciliationContext,
) -> tuple[ReconciliationDecision, ...]:
    """Classify synthetic ledger drift and return bounded action decisions."""

    exchange_by_instrument: dict[str, list[ExchangePosition]] = defaultdict(list)
    local_by_instrument: dict[str, list[LocalPosition]] = defaultdict(list)
    for position in context.exchange_positions:
        exchange_by_instrument[position.key.instrument].append(position)
    for position in context.local_positions:
        local_by_instrument[position.key.instrument].append(position)

    decisions: list[ReconciliationDecision] = []
    instruments = sorted(set(exchange_by_instrument) | set(local_by_instrument))
    for instrument in instruments:
        exchanges = exchange_by_instrument[instrument]
        locals_ = local_by_instrument[instrument]

        if len(exchanges) > 1 or len(locals_) > 1:
            key = (exchanges[0].key if exchanges else locals_[0].key)
            decisions.append(
                _decision(
                    _finding(
                        FindingKind.AMBIGUOUS_OBSERVATION,
                        Severity.CRITICAL,
                        key,
                        "multiple observations make ownership ambiguous",
                    ),
                    (_human("ambiguous duplicate observations require human review"),),
                    context,
                    exchanges[0].owner_tag if exchanges else None,
                )
            )
            continue

        if exchanges and locals_:
            exchange = exchanges[0]
            local = locals_[0]
            if exchange.key.side is not local.key.side:
                decisions.append(_direction_mismatch(exchange, local, context))
            else:
                decisions.append(_paired(exchange, local, context))
        elif exchanges:
            decisions.append(_exchange_only(exchanges[0], context))
        elif locals_:
            decisions.append(_local_only(locals_[0], context))

    return tuple(decisions)
