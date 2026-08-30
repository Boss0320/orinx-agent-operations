from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


try:
    from scripts.check_public_boundary import scan_tree
except ModuleNotFoundError:
    scan_tree = None


class PublicBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            scan_tree,
            "public-boundary scanner is not implemented",
        )

    def scan_text(self, content: str):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "candidate.md").write_text(content, encoding="utf-8")
            return scan_tree(root)

    def test_rejects_private_path(self):
        findings = self.scan_text("/" + "Users/example/private.txt")

        self.assertEqual(
            {finding.rule for finding in findings},
            {"private_path"},
        )

    def test_rejects_secret_assignment(self):
        findings = self.scan_text("API" + "_KEY = 'synthetic-but-secret-looking'")

        self.assertEqual(
            {finding.rule for finding in findings},
            {"secret_assignment"},
        )

    def test_rejects_unquoted_secret_assignment(self):
        findings = self.scan_text("TOKEN" + "=synthetic-secret-value")

        self.assertEqual(
            {finding.rule for finding in findings},
            {"secret_assignment"},
        )

    def test_rejects_private_key_header(self):
        findings = self.scan_text("-----BEGIN " + "PRIVATE KEY-----")

        self.assertEqual(
            {finding.rule for finding in findings},
            {"private_key"},
        )

    def test_rejects_account_identifier(self):
        findings = self.scan_text("account" + "_id: 123456")

        self.assertEqual(
            {finding.rule for finding in findings},
            {"account_identifier"},
        )

    def test_rejects_quantified_performance_claim(self):
        findings = self.scan_text("win " + "rate: 80%")

        self.assertEqual(
            {finding.rule for finding in findings},
            {"performance_claim"},
        )

    def test_rejects_prohibited_positioning_phrase(self):
        findings = self.scan_text("fully " + "autonomous trading agent")

        self.assertEqual(
            {finding.rule for finding in findings},
            {"prohibited_positioning"},
        )

    def test_rejects_current_live_claim(self):
        findings = self.scan_text("The system is currently " + "live.")

        self.assertEqual(
            {finding.rule for finding in findings},
            {"current_live_claim"},
        )

    def test_rejects_dotenv_file_even_when_its_contents_look_safe(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env").write_text("SAFE_MODE=1", encoding="utf-8")

            findings = scan_tree(root)

        self.assertEqual(
            {finding.rule for finding in findings},
            {"environment_file"},
        )

    def test_rejects_unrecognized_file_types_instead_of_skipping_them(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "runtime.db").write_bytes(b"synthetic runtime bytes")

            findings = scan_tree(root)

            self.assertEqual(
                {finding.rule for finding in findings},
                {"unexpected_file"},
            )

    def test_rejects_python_runtime_cache_directories(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cache = root / "__pycache__"
            cache.mkdir()
            (cache / "module.cpython-314.pyc").write_bytes(b"synthetic-cache")

            findings = scan_tree(root)

            self.assertEqual(
                {finding.rule for finding in findings},
                {"runtime_cache"},
            )

    def test_rejects_symlink_in_public_tree(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.md"
            target.write_text("safe synthetic content", encoding="utf-8")
            (root / "linked.md").symlink_to(target)

            findings = scan_tree(root)

        self.assertEqual(
            {finding.rule for finding in findings},
            {"symlink"},
        )

    def test_allows_synthetic_instrument(self):
        self.assertEqual(self.scan_text("instrument: SYNTH-ALPHA"), ())

    def test_allows_bounded_autonomy_copy(self):
        self.assertEqual(
            self.scan_text("Bounded autonomy with human escalation."),
            (),
        )

    def test_finding_excerpt_is_redacted_and_bounded(self):
        findings = self.scan_text("API" + "_KEY = 'abcdefghijklmnopqrstuvwxyz'")

        self.assertLessEqual(len(findings[0].excerpt), 80)
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz", findings[0].excerpt)


if __name__ == "__main__":
    unittest.main()
