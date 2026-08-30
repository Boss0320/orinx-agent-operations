"""Deterministic CLI examples for the reconciliation case."""

from datetime import UTC, datetime
import json

from .engine import reconcile
from .model import (
    CloseEvidence,
    ExchangePosition,
    LocalPosition,
    OwnerTag,
    PositionKey,
    PositionSide,
    PositionStatus,
    ReconciliationContext,
)


OBSERVED_AT = datetime(2026, 1, 15, 12, tzinfo=UTC)


def _serialize(scenario: str, context: ReconciliationContext) -> dict[str, str]:
    decision = reconcile(context)[0]
    action = decision.actions[0]
    return {
        "action": action.kind.value,
        "authority": action.authority.value,
        "finding": decision.finding.kind.value,
        "instrument": decision.finding.key.instrument,
        "mutation_target": action.mutation_target.value,
        "scenario": scenario,
    }


def build_examples() -> tuple[dict[str, str], ...]:
    """Return three fixed scenarios with distinct authority outcomes."""

    aligned_key = PositionKey("SYNTH-ALPHA", PositionSide.LONG)
    local_only_key = PositionKey("SYNTH-BETA", PositionSide.SHORT)
    unknown_key = PositionKey("SYNTH-GAMMA", PositionSide.LONG)

    return (
        _serialize(
            "aligned",
            ReconciliationContext(
                exchange_positions=(
                    ExchangePosition(
                        aligned_key,
                        3,
                        OwnerTag.SYSTEM,
                        PositionStatus.OPEN,
                    ),
                ),
                local_positions=(
                    LocalPosition(aligned_key, PositionStatus.OPEN, 3),
                ),
                close_evidence=(),
                transient_exit_failures=(),
                kill_switch_active=False,
                observed_at=OBSERVED_AT,
            ),
        ),
        _serialize(
            "verified_local_only",
            ReconciliationContext(
                exchange_positions=(),
                local_positions=(
                    LocalPosition(local_only_key, PositionStatus.OPEN, 2),
                ),
                close_evidence=(
                    CloseEvidence(local_only_key, True, OBSERVED_AT),
                ),
                transient_exit_failures=(),
                kill_switch_active=False,
                observed_at=OBSERVED_AT,
            ),
        ),
        _serialize(
            "unknown_exchange_only",
            ReconciliationContext(
                exchange_positions=(
                    ExchangePosition(
                        unknown_key,
                        1,
                        OwnerTag.UNKNOWN,
                        PositionStatus.OPEN,
                    ),
                ),
                local_positions=(),
                close_evidence=(),
                transient_exit_failures=(),
                kill_switch_active=False,
                observed_at=OBSERVED_AT,
            ),
        ),
    )


def render_examples() -> str:
    """Serialize the fixed examples as stable, human-readable JSON."""

    return json.dumps(build_examples(), ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    print(render_examples())
