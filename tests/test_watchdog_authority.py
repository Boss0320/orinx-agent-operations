from datetime import UTC, datetime, timedelta
import unittest


try:
    from demo.watchdog_authority.engine import evaluate_issue
    from demo.watchdog_authority.model import (
        ActionKind,
        AuthorityTier,
        IssueKind,
        NotificationState,
        WatchdogContext,
        WatchdogIssue,
    )
except ModuleNotFoundError as error:
    IMPORT_ERROR = error
else:
    IMPORT_ERROR = None


NOW = datetime(2026, 1, 15, 12, tzinfo=UTC)


class WatchdogAuthorityTests(unittest.TestCase):
    def setUp(self):
        if IMPORT_ERROR is not None:
            self.fail(f"watchdog authority feature is not implemented: {IMPORT_ERROR}")

    def test_first_allowlisted_service_failure_can_restart_once(self):
        result = evaluate_issue(
            WatchdogContext(
                issue=WatchdogIssue(IssueKind.SERVICE_DOWN, 1, NOW),
                notification=NotificationState(None, 0),
                external_heartbeat_present=True,
                now=NOW,
            )
        )

        self.assertEqual(result.action, ActionKind.RESTART_ALLOWLISTED_SERVICE)
        self.assertEqual(result.authority, AuthorityTier.AUTO_FIX)
        self.assertFalse(result.healthy)

    def test_repeated_service_failure_escalates_to_human(self):
        result = evaluate_issue(
            WatchdogContext(
                issue=WatchdogIssue(IssueKind.SERVICE_DOWN, 3, NOW),
                notification=NotificationState(NOW - timedelta(minutes=20), 1),
                external_heartbeat_present=True,
                now=NOW,
            )
        )

        self.assertEqual(result.action, ActionKind.NOTIFY_HUMAN)
        self.assertEqual(result.authority, AuthorityTier.HUMAN_REQUIRED)

    def test_corrupt_state_is_never_autofixed(self):
        result = evaluate_issue(
            WatchdogContext(
                issue=WatchdogIssue(IssueKind.CORRUPT_STATE, 1, NOW),
                notification=NotificationState(None, 0),
                external_heartbeat_present=True,
                now=NOW,
            )
        )

        self.assertEqual(result.action, ActionKind.NOTIFY_HUMAN)
        self.assertEqual(result.authority, AuthorityTier.HUMAN_REQUIRED)

    def test_missing_external_heartbeat_never_reports_health(self):
        result = evaluate_issue(
            WatchdogContext(
                issue=None,
                notification=NotificationState(None, 0),
                external_heartbeat_present=False,
                now=NOW,
            )
        )

        self.assertEqual(result.action, ActionKind.NOTIFY_HUMAN)
        self.assertFalse(result.healthy)

    def test_notification_is_deduped_inside_cooldown(self):
        result = evaluate_issue(
            WatchdogContext(
                issue=WatchdogIssue(IssueKind.STALE_PIPELINE, 1, NOW),
                notification=NotificationState(NOW - timedelta(minutes=5), 1),
                external_heartbeat_present=True,
                now=NOW,
            )
        )

        self.assertEqual(result.action, ActionKind.SUPPRESS_DUPLICATE)
        self.assertEqual(result.authority, AuthorityTier.AGENT_REVIEW)
        self.assertFalse(result.healthy)

    def test_unknown_issue_requires_human(self):
        result = evaluate_issue(
            WatchdogContext(
                issue=WatchdogIssue(IssueKind.UNKNOWN, 1, NOW),
                notification=NotificationState(None, 0),
                external_heartbeat_present=True,
                now=NOW,
            )
        )

        self.assertEqual(result.action, ActionKind.NOTIFY_HUMAN)
        self.assertEqual(result.authority, AuthorityTier.HUMAN_REQUIRED)

    def test_stale_ephemeral_trigger_is_allowlisted_auto_fix(self):
        result = evaluate_issue(
            WatchdogContext(
                issue=WatchdogIssue(IssueKind.STALE_TRIGGER, 1, NOW),
                notification=NotificationState(None, 0),
                external_heartbeat_present=True,
                now=NOW,
            )
        )

        self.assertEqual(result.action, ActionKind.REBUILD_EPHEMERAL_TRIGGER)
        self.assertEqual(result.authority, AuthorityTier.AUTO_FIX)

    def test_notification_cooldown_does_not_suppress_allowlisted_repair(self):
        result = evaluate_issue(
            WatchdogContext(
                issue=WatchdogIssue(IssueKind.STALE_TRIGGER, 1, NOW),
                notification=NotificationState(NOW - timedelta(minutes=5), 1),
                external_heartbeat_present=True,
                now=NOW,
            )
        )

        self.assertEqual(result.action, ActionKind.REBUILD_EPHEMERAL_TRIGGER)
        self.assertEqual(result.authority, AuthorityTier.AUTO_FIX)

    def test_second_service_failure_routes_to_agent_instead_of_restarting_again(self):
        result = evaluate_issue(
            WatchdogContext(
                issue=WatchdogIssue(IssueKind.SERVICE_DOWN, 2, NOW),
                notification=NotificationState(None, 0),
                external_heartbeat_present=True,
                now=NOW,
            )
        )

        self.assertEqual(result.action, ActionKind.NOTIFY_AGENT)
        self.assertEqual(result.authority, AuthorityTier.AGENT_REVIEW)

    def test_stale_pipeline_routes_to_agent_review(self):
        result = evaluate_issue(
            WatchdogContext(
                issue=WatchdogIssue(IssueKind.STALE_PIPELINE, 1, NOW),
                notification=NotificationState(None, 0),
                external_heartbeat_present=True,
                now=NOW,
            )
        )

        self.assertEqual(result.action, ActionKind.NOTIFY_AGENT)
        self.assertEqual(result.authority, AuthorityTier.AGENT_REVIEW)


if __name__ == "__main__":
    unittest.main()
