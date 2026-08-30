from datetime import UTC, datetime
import unittest

from demo.reconciliation.model import (
    ExchangePosition,
    LocalPosition,
    OwnerTag,
    PositionKey,
    PositionSide,
    PositionStatus,
)
from demo.watchdog_authority.model import IssueKind, NotificationState, WatchdogIssue


NOW = datetime(2026, 1, 15, 12, tzinfo=UTC)


class InputContractTests(unittest.TestCase):
    def test_non_synthetic_instrument_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "synthetic instrument"):
            PositionKey("BTC" + "-USDT", PositionSide.LONG)

    def test_non_positive_position_quantity_is_rejected(self):
        key = PositionKey("SYNTH-KAPPA", PositionSide.SHORT)

        with self.assertRaisesRegex(ValueError, "positive"):
            ExchangePosition(key, 0, OwnerTag.SYSTEM, PositionStatus.OPEN)

        with self.assertRaisesRegex(ValueError, "positive"):
            LocalPosition(key, PositionStatus.OPEN, 0)

    def test_watchdog_issue_count_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            WatchdogIssue(IssueKind.SERVICE_DOWN, 0, NOW)

    def test_notification_count_cannot_be_negative(self):
        with self.assertRaisesRegex(ValueError, "negative"):
            NotificationState(None, -1)


if __name__ == "__main__":
    unittest.main()
