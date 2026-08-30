from __future__ import annotations

from pathlib import Path
import re
import unittest
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
EN_README = (ROOT / "README.md").read_text(encoding="utf-8")
ZH_README = (ROOT / "README.zh-TW.md").read_text(encoding="utf-8")
EN_CASE = (ROOT / "docs" / "when-agent-and-exchange-disagree.md").read_text(
    encoding="utf-8"
)
ZH_CASE = (ROOT / "docs" / "when-agent-and-exchange-disagree.zh-TW.md").read_text(
    encoding="utf-8"
)


def assert_ordered(
    testcase: unittest.TestCase, source: str, markers: tuple[str, ...]
) -> None:
    positions: list[int] = []
    for marker in markers:
        testcase.assertIn(marker, source)
        positions.append(source.index(marker))
    testcase.assertEqual(positions, sorted(positions))


class PackagingContractTests(unittest.TestCase):
    def test_readme_heroes_separate_product_descriptor_thesis_and_ownership(self) -> None:
        assert_ordered(
            self,
            EN_README,
            (
                "# ORINX",
                "Agentic Trading Operations Under External Side Effects",
                "When the agent and the exchange disagree, the system must know "
                "which state is allowed to authorize the next action.",
                "Created and operated by Titus Lai.",
            ),
        )
        assert_ordered(
            self,
            ZH_README,
            (
                "# ORINX",
                "外部副作用下的 Agentic 交易營運系統",
                "當 Agent 與交易所互相矛盾，系統必須知道哪一份 state "
                "有權批准下一個動作。",
                "由 Titus Lai 建立並營運。",
            ),
        )
        self.assertEqual(EN_README.count("\n# ORINX\n"), 1)
        self.assertEqual(ZH_README.count("\n# ORINX\n"), 1)
        self.assertIn("During long-running operation, ORINX monitored markets", EN_README)
        self.assertIn("在長期運作期間，ORINX 曾持續監控市場", ZH_README)

    def test_readme_incident_arc_precedes_clean_room_boundary(self) -> None:
        english_stages = (
            "## The incident that changed the architecture",
            "### Before",
            "### Failure",
            "### Decision",
            "### Permanent fix",
        )
        chinese_stages = (
            "## 改變架構的那次事故",
            "### 出事前",
            "### 故障",
            "### 決策",
            "### 永久修復",
        )
        assert_ordered(self, EN_README, english_stages)
        assert_ordered(self, ZH_README, chinese_stages)
        self.assertGreater(EN_README.lower().index("clean-room"), EN_README.index("### Permanent fix"))
        self.assertGreater(ZH_README.lower().index("clean-room"), ZH_README.index("### 永久修復"))

    def test_flagship_articles_open_with_the_same_four_stage_reconstruction(self) -> None:
        assert_ordered(
            self,
            EN_CASE,
            (
                "# When the Agent and the Exchange Disagree",
                "## Incident reconstruction",
                "### Before",
                "### Failure",
                "### Decision",
                "### Permanent fix",
                "## The problem",
            ),
        )
        assert_ordered(
            self,
            ZH_CASE,
            (
                "# 當 Agent 與交易所互相矛盾",
                "## 事故重建",
                "### 出事前",
                "### 故障",
                "### 決策",
                "### 永久修復",
                "## 問題",
            ),
        )

    def test_failure_timeline_is_a_mobile_first_split_authority_state_board(self) -> None:
        path = ROOT / "assets" / "failure-timeline.svg"
        source = path.read_text(encoding="utf-8")
        root = ET.fromstring(source)
        rendered_text = " ".join(text.strip() for text in root.itertext() if text.strip())

        self.assertEqual(root.attrib["viewBox"], "0 0 390 1040")
        for marker in (
            "LOCAL LEDGER",
            "EXCHANGE",
            "LOCAL CLOSED",
            "EXCHANGE OPEN",
            "PRESERVE BOTH STATES",
            "BOUNDED RETRY",
            "HUMAN BOUNDARY",
        ):
            self.assertIn(marker, rendered_text)
        font_sizes = [float(value) for value in re.findall(r"font:[^;{}]*?(\d+(?:\.\d+)?)px", source)]
        self.assertTrue(font_sizes)
        self.assertGreaterEqual(min(font_sizes), 16)


if __name__ == "__main__":
    unittest.main()
