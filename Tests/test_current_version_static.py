"""Keep the user-visible version sources aligned for the next release."""

from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]


class CurrentVersionStaticTests(unittest.TestCase):
    def test_marketing_and_build_versions_are_0_1_50_build_53(self):
        plist = (ROOT / "Platforms/macOS/App/Info.plist").read_text()
        panel = (ROOT / "Platforms/macOS/App/ZYCandidatePanel.mm").read_text()
        readme = (ROOT / "README.md").read_text()
        changelog = (ROOT / "CHANGELOG.md").read_text()
        html = (ROOT / "Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html").read_text()
        self.assertIn("<string>0.1.50</string>", plist)
        self.assertIn("<string>53</string>", plist)
        self.assertIn('[@"v0.1.50"', panel)
        self.assertIn("v0.1.50 / build 53", readme)
        self.assertIn("## v0.1.50 / build 53", changelog)
        self.assertIn("逐音輸入法  v0.1.50", html)


if __name__ == "__main__":
    unittest.main()
