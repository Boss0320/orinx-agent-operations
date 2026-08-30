import json
import unittest


try:
    from demo.watchdog_authority.example import build_examples, render_examples
except ModuleNotFoundError as error:
    IMPORT_ERROR = error
else:
    IMPORT_ERROR = None


class WatchdogExampleTests(unittest.TestCase):
    def setUp(self):
        if IMPORT_ERROR is not None:
            self.fail(f"watchdog example is not implemented: {IMPORT_ERROR}")

    def test_example_covers_four_authority_boundaries(self):
        examples = build_examples()

        self.assertEqual(
            [example["scenario"] for example in examples],
            [
                "allowlisted_restart",
                "corrupt_state",
                "notification_cooldown",
                "missing_external_heartbeat",
            ],
        )
        self.assertEqual(examples[1]["authority"], "human_required")
        self.assertEqual(examples[3]["authority"], "human_required")

    def test_rendered_example_is_stable_json(self):
        first = render_examples()
        second = render_examples()

        self.assertEqual(first, second)
        self.assertEqual(len(json.loads(first)), 4)
        self.assertNotIn("command", first.lower())
        self.assertNotIn("process", first.lower())


if __name__ == "__main__":
    unittest.main()
