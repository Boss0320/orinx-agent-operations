import json
import unittest


try:
    from demo.reconciliation.example import build_examples, render_examples
except ModuleNotFoundError as error:
    IMPORT_ERROR = error
else:
    IMPORT_ERROR = None


class ReconciliationExampleTests(unittest.TestCase):
    def setUp(self):
        if IMPORT_ERROR is not None:
            self.fail(f"reconciliation example is not implemented: {IMPORT_ERROR}")

    def test_example_covers_three_distinct_authority_outcomes(self):
        examples = build_examples()

        self.assertEqual(
            [example["scenario"] for example in examples],
            ["aligned", "verified_local_only", "unknown_exchange_only"],
        )
        self.assertEqual(
            [example["action"] for example in examples],
            ["noop", "settle_local", "alert_human"],
        )

    def test_rendered_example_is_stable_json(self):
        first = render_examples()
        second = render_examples()

        self.assertEqual(first, second)
        self.assertEqual(len(json.loads(first)), 3)
        self.assertNotIn("account", first.lower())
        self.assertNotIn("strategy", first.lower())


if __name__ == "__main__":
    unittest.main()
