from datetime import UTC, datetime, timedelta
import unittest


try:
    from demo.reconciliation.engine import reconcile
    from demo.reconciliation.model import (
        ActionKind,
        AuthorityTier,
        CloseEvidence,
        ExchangePosition,
        FindingKind,
        LocalPosition,
        MutationTarget,
        OwnerTag,
        PositionKey,
        PositionSide,
        PositionStatus,
        ReconciliationContext,
    )
except ModuleNotFoundError as error:
    IMPORT_ERROR = error
else:
    IMPORT_ERROR = None


NOW = datetime(2026, 1, 15, 12, tzinfo=UTC)


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        if IMPORT_ERROR is not None:
            self.fail(f"reconciliation feature is not implemented: {IMPORT_ERROR}")

    def test_unknown_exchange_owner_fails_closed_to_human(self):
        key = PositionKey("SYNTH-ALPHA", PositionSide.LONG)
        decisions = reconcile(
            ReconciliationContext(
                exchange_positions=(
                    ExchangePosition(key, 3, OwnerTag.UNKNOWN, PositionStatus.OPEN),
                ),
                local_positions=(),
                close_evidence=(),
                transient_exit_failures=(),
                kill_switch_active=False,
                observed_at=NOW,
            )
        )

        self.assertEqual(decisions[0].finding.kind, FindingKind.EXCHANGE_ONLY)
        self.assertEqual(decisions[0].actions[0].kind, ActionKind.ALERT_HUMAN)
        self.assertEqual(
            decisions[0].actions[0].authority,
            AuthorityTier.HUMAN_REQUIRED,
        )
        self.assertEqual(
            decisions[0].actions[0].mutation_target,
            MutationTarget.NONE,
        )

    def test_manual_exchange_position_is_never_mutated(self):
        key = PositionKey("SYNTH-BETA", PositionSide.SHORT)
        decisions = reconcile(
            ReconciliationContext(
                exchange_positions=(
                    ExchangePosition(key, 2, OwnerTag.MANUAL, PositionStatus.OPEN),
                ),
                local_positions=(),
                close_evidence=(),
                transient_exit_failures=(),
                kill_switch_active=False,
                observed_at=NOW,
            )
        )

        self.assertEqual(
            decisions[0].actions[0].kind,
            ActionKind.LEAVE_UNTOUCHED,
        )
        self.assertEqual(
            decisions[0].actions[0].mutation_target,
            MutationTarget.NONE,
        )

    def test_verified_local_only_position_can_settle_local_ledger(self):
        key = PositionKey("SYNTH-GAMMA", PositionSide.LONG)
        decisions = reconcile(
            ReconciliationContext(
                exchange_positions=(),
                local_positions=(LocalPosition(key, PositionStatus.OPEN, 5),),
                close_evidence=(CloseEvidence(key, True, NOW),),
                transient_exit_failures=(),
                kill_switch_active=False,
                observed_at=NOW,
            )
        )

        self.assertEqual(decisions[0].finding.kind, FindingKind.LOCAL_ONLY)
        self.assertEqual(decisions[0].actions[0].kind, ActionKind.SETTLE_LOCAL)
        self.assertEqual(decisions[0].actions[0].authority, AuthorityTier.AUTO_FIX)
        self.assertEqual(
            decisions[0].actions[0].mutation_target,
            MutationTarget.LOCAL_LEDGER,
        )

    def test_stale_close_evidence_cannot_settle_a_reopened_local_position(self):
        key = PositionKey("SYNTH-GAMMA", PositionSide.LONG)
        decisions = reconcile(
            ReconciliationContext(
                exchange_positions=(),
                local_positions=(LocalPosition(key, PositionStatus.OPEN, 5),),
                close_evidence=(CloseEvidence(key, True, NOW - timedelta(days=365)),),
                transient_exit_failures=(),
                kill_switch_active=False,
                observed_at=NOW,
            )
        )

        self.assertEqual(decisions[0].actions[0].kind, ActionKind.ALERT_HUMAN)

    def test_future_close_evidence_cannot_authorize_local_settlement(self):
        key = PositionKey("SYNTH-GAMMA", PositionSide.LONG)
        decisions = reconcile(
            ReconciliationContext(
                exchange_positions=(),
                local_positions=(LocalPosition(key, PositionStatus.OPEN, 5),),
                close_evidence=(CloseEvidence(key, True, NOW + timedelta(seconds=1)),),
                transient_exit_failures=(),
                kill_switch_active=False,
                observed_at=NOW,
            )
        )

        self.assertEqual(decisions[0].actions[0].kind, ActionKind.ALERT_HUMAN)

    def test_close_evidence_from_a_prior_position_lifecycle_is_rejected(self):
        try:
            current_key = PositionKey(
                "SYNTH-GAMMA",
                PositionSide.LONG,
                lifecycle_id="SYNTH-LIFE-CURRENT",
            )
            prior_key = PositionKey(
                "SYNTH-GAMMA",
                PositionSide.LONG,
                lifecycle_id="SYNTH-LIFE-PRIOR",
            )
        except TypeError:
            self.fail("position identity must include a synthetic lifecycle id")

        decisions = reconcile(
            ReconciliationContext(
                exchange_positions=(),
                local_positions=(LocalPosition(current_key, PositionStatus.OPEN, 5),),
                close_evidence=(CloseEvidence(prior_key, True, NOW),),
                transient_exit_failures=(),
                kill_switch_active=False,
                observed_at=NOW,
            )
        )

        self.assertEqual(decisions[0].actions[0].kind, ActionKind.ALERT_HUMAN)

    def test_unverified_local_only_position_requires_human(self):
        key = PositionKey("SYNTH-DELTA", PositionSide.LONG)
        decisions = reconcile(
            ReconciliationContext(
                exchange_positions=(),
                local_positions=(LocalPosition(key, PositionStatus.OPEN, 5),),
                close_evidence=(),
                transient_exit_failures=(),
                kill_switch_active=False,
                observed_at=NOW,
            )
        )

        self.assertEqual(
            decisions[0].actions[0].authority,
            AuthorityTier.HUMAN_REQUIRED,
        )

    def test_direction_mismatch_never_autofixes(self):
        exchange_key = PositionKey("SYNTH-EPSILON", PositionSide.LONG)
        local_key = PositionKey("SYNTH-EPSILON", PositionSide.SHORT)
        decisions = reconcile(
            ReconciliationContext(
                exchange_positions=(
                    ExchangePosition(
                        exchange_key,
                        1,
                        OwnerTag.SYSTEM,
                        PositionStatus.OPEN,
                    ),
                ),
                local_positions=(LocalPosition(local_key, PositionStatus.OPEN, 1),),
                close_evidence=(),
                transient_exit_failures=(),
                kill_switch_active=False,
                observed_at=NOW,
            )
        )

        self.assertEqual(
            decisions[0].finding.kind,
            FindingKind.DIRECTION_MISMATCH,
        )
        self.assertTrue(
            all(
                action.authority is AuthorityTier.HUMAN_REQUIRED
                for action in decisions[0].actions
            )
        )

    def test_different_position_lifecycles_never_report_aligned(self):
        exchange_key = PositionKey(
            "SYNTH-EPSILON",
            PositionSide.LONG,
            lifecycle_id="SYNTH-LIFE-EXCHANGE",
        )
        local_key = PositionKey(
            "SYNTH-EPSILON",
            PositionSide.LONG,
            lifecycle_id="SYNTH-LIFE-LOCAL",
        )
        decisions = reconcile(
            ReconciliationContext(
                exchange_positions=(
                    ExchangePosition(
                        exchange_key,
                        1,
                        OwnerTag.SYSTEM,
                        PositionStatus.OPEN,
                    ),
                ),
                local_positions=(LocalPosition(local_key, PositionStatus.OPEN, 1),),
                close_evidence=(),
                transient_exit_failures=(),
                kill_switch_active=False,
                observed_at=NOW,
            )
        )

        self.assertEqual(
            decisions[0].finding.kind,
            FindingKind.LIFECYCLE_MISMATCH,
        )
        self.assertEqual(decisions[0].actions[0].kind, ActionKind.ALERT_HUMAN)
        self.assertEqual(
            decisions[0].actions[0].authority,
            AuthorityTier.HUMAN_REQUIRED,
        )

    def test_closed_exchange_and_open_local_is_state_mismatch(self):
        key = PositionKey("SYNTH-THETA", PositionSide.LONG)
        decisions = reconcile(
            ReconciliationContext(
                exchange_positions=(
                    ExchangePosition(key, 3, OwnerTag.SYSTEM, PositionStatus.CLOSED),
                ),
                local_positions=(LocalPosition(key, PositionStatus.OPEN, 3),),
                close_evidence=(),
                transient_exit_failures=(),
                kill_switch_active=False,
                observed_at=NOW,
            )
        )

        self.assertEqual(decisions[0].finding.kind.value, "state_mismatch")
        self.assertEqual(
            decisions[0].actions[0].authority,
            AuthorityTier.HUMAN_REQUIRED,
        )

    def test_duplicate_observations_are_ambiguous_not_quantity_mismatch(self):
        first = PositionKey("SYNTH-IOTA", PositionSide.LONG)
        second = PositionKey("SYNTH-IOTA", PositionSide.SHORT)
        decisions = reconcile(
            ReconciliationContext(
                exchange_positions=(
                    ExchangePosition(first, 1, OwnerTag.SYSTEM, PositionStatus.OPEN),
                    ExchangePosition(second, 1, OwnerTag.MANUAL, PositionStatus.OPEN),
                ),
                local_positions=(),
                close_evidence=(),
                transient_exit_failures=(),
                kill_switch_active=False,
                observed_at=NOW,
            )
        )

        self.assertEqual(
            decisions[0].finding.kind.value,
            "ambiguous_observation",
        )
        self.assertEqual(
            decisions[0].actions[0].authority,
            AuthorityTier.HUMAN_REQUIRED,
        )

    def test_kill_switch_blocks_retry_exchange_close(self):
        key = PositionKey("SYNTH-ZETA", PositionSide.LONG)
        decisions = reconcile(
            ReconciliationContext(
                exchange_positions=(
                    ExchangePosition(key, 4, OwnerTag.SYSTEM, PositionStatus.OPEN),
                ),
                local_positions=(LocalPosition(key, PositionStatus.CLOSED, 4),),
                close_evidence=(),
                transient_exit_failures=((key, 1),),
                kill_switch_active=True,
                observed_at=NOW,
            )
        )

        actions = decisions[0].actions
        self.assertNotIn(
            ActionKind.RETRY_EXCHANGE_CLOSE,
            {action.kind for action in actions},
        )
        self.assertEqual(actions[0].kind, ActionKind.ALERT_HUMAN)

    def test_transient_system_exit_failure_retries_once_when_enabled(self):
        key = PositionKey("SYNTH-ETA", PositionSide.SHORT)
        decisions = reconcile(
            ReconciliationContext(
                exchange_positions=(
                    ExchangePosition(key, 2, OwnerTag.SYSTEM, PositionStatus.OPEN),
                ),
                local_positions=(LocalPosition(key, PositionStatus.CLOSED, 2),),
                close_evidence=(),
                transient_exit_failures=((key, 1),),
                kill_switch_active=False,
                observed_at=NOW,
            )
        )

        self.assertEqual(
            decisions[0].actions[0].kind,
            ActionKind.RETRY_EXCHANGE_CLOSE,
        )
        self.assertEqual(
            decisions[0].actions[0].authority,
            AuthorityTier.AUTO_FIX,
        )
        self.assertEqual(
            decisions[0].actions[0].mutation_target,
            MutationTarget.EXCHANGE,
        )


if __name__ == "__main__":
    unittest.main()
