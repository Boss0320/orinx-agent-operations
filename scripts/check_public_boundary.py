"""Default-deny text scan for the clean public source tree."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sys


PUBLIC_EXTENSIONS = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".svg",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
IGNORED_PARTS = {".git"}
RUNTIME_CACHE_PARTS = {"__pycache__"}
PUBLIC_TEXT_FILENAMES = {".gitignore", "LICENSE"}


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    rule: str
    excerpt: str


def _compiled_rules() -> tuple[tuple[str, re.Pattern[str]], ...]:
    private_path = r"/" + r"Users/|Desktop/" + r"ORINX"
    secret_name = r"api[_ -]?" + r"key|secret|token|password"
    secret_value = r"(?:['\"][^'\"]+['\"]|[^\s#]+)"
    secret_assignment = rf"(?i)(?:{secret_name})\s*[:=]\s*{secret_value}"
    identifier_name = r"account|order|telegram"
    account_identifier = rf"(?i)(?:{identifier_name})[_ -]?id\s*[:=]"
    performance_term = r"win\s*rate|pnl|account\s*size"
    performance_claim = rf"(?i)(?:{performance_term})\s*[:=]?\s*[-+$]?\d"
    prohibited_phrases = (
        "fully " + "autonomous",
        "self-" + "healing",
        "validated " + "edge",
        "guaranteed " + "alpha",
        "profitable " + "ai",
    )
    prohibited_positioning = "(?i)(?:" + "|".join(
        re.escape(phrase) for phrase in prohibited_phrases
    ) + ")"
    private_key = r"-----BEGIN\s+" + r"(?:RSA\s+|EC\s+|OPENSSH\s+)?PRIVATE\s+KEY-----"
    current_live_claim = r"(?i)currently\s+" + r"live\b"
    non_synthetic_instrument = r"['\"](?!SYNTH-)[A-Z0-9]{2,12}[-/][A-Z0-9]{2,12}['\"]"
    return (
        ("private_path", re.compile(private_path, re.IGNORECASE)),
        ("secret_assignment", re.compile(secret_assignment)),
        ("account_identifier", re.compile(account_identifier)),
        ("performance_claim", re.compile(performance_claim)),
        ("prohibited_positioning", re.compile(prohibited_positioning)),
        ("private_key", re.compile(private_key)),
        ("current_live_claim", re.compile(current_live_claim)),
        ("non_synthetic_instrument", re.compile(non_synthetic_instrument)),
    )


RULES = _compiled_rules()


def _safe_excerpt(rule: str) -> str:
    return f"<{rule} content redacted>"[:80]


def _iter_public_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(
            part in IGNORED_PARTS or part in RUNTIME_CACHE_PARTS
            for part in relative.parts
        ):
            continue
        yield path, relative


def scan_tree(root: Path) -> tuple[Finding, ...]:
    """Return stable findings for prohibited public content under ``root``."""

    findings: list[Finding] = []
    for path in sorted(root.rglob("*")):
        if path.is_dir() and path.name in RUNTIME_CACHE_PARTS:
            findings.append(
                Finding(
                    str(path.relative_to(root)),
                    1,
                    "runtime_cache",
                    "<runtime cache directory>",
                )
            )
            continue
        if path.is_symlink():
            findings.append(
                Finding(
                    str(path.relative_to(root)),
                    1,
                    "symlink",
                    "<symlink target redacted>",
                )
            )
    for path, relative in _iter_public_files(root):
        if path.name == ".env" or path.name.startswith(".env."):
            findings.append(
                Finding(str(relative), 1, "environment_file", "<environment file>")
            )
            continue
        if (
            path.suffix.lower() not in PUBLIC_EXTENSIONS
            and path.name not in PUBLIC_TEXT_FILENAMES
        ):
            findings.append(
                Finding(str(relative), 1, "unexpected_file", "<unexpected file>")
            )
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            findings.append(
                Finding(str(relative), 1, "non_utf8_text", "<non-UTF-8 content>")
            )
            continue
        for line_number, line in enumerate(lines, start=1):
            for rule, pattern in RULES:
                if pattern.search(line):
                    findings.append(
                        Finding(
                            str(relative),
                            line_number,
                            rule,
                            _safe_excerpt(rule),
                        )
                    )
    return tuple(sorted(findings))


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    root = Path(args[0] if args else ".")
    findings = scan_tree(root)
    print(json.dumps([asdict(item) for item in findings], indent=2, sort_keys=True))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
