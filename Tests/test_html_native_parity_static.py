"""Regression guards for native-style behavior in the Canvas demo."""

from pathlib import Path
import unittest


HTML = Path(__file__).parents[1] / "Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html"


class HtmlNativeParityStaticTests(unittest.TestCase):
    def test_option_only_deletes_candidates_that_have_learning(self):
        source = HTML.read_text()
        self.assertIn("function removeCandidateLearning(candidate)", source)
        self.assertIn("learned:!!x.learned", source)
        self.assertIn("state.optionDown && c.learned", source)
        self.assertIn("removeCandidateLearning(state.candidates[hit.index])", source)

    def test_switching_to_english_commits_unfinished_chinese(self):
        source = HTML.read_text()
        start = source.index("function switchInputMode()")
        end = source.index("function switchOutputScript()", start)
        switcher = source[start:end]
        self.assertIn("if(state.inputMode==='zh' && state.composition)", switcher)
        self.assertIn("commitCandidate()", switcher)
        self.assertIn("finalizePending()", switcher)

    def test_candidate_panel_uses_native_style_adaptive_grid_and_control_rail(self):
        source = HTML.read_text()
        self.assertIn("function candidateColumns()", source)
        self.assertIn("railW=64", source)
        self.assertIn("'toggleHelp'", source)
        self.assertIn("'clearLearning'", source)

    def test_control_rail_stays_inside_the_candidate_panel(self):
        source = HTML.read_text()
        self.assertIn("const railButtonH=18", source)
        self.assertIn("const railGap=3", source)
        self.assertIn("candidateY+10+i*(railButtonH+railGap)", source)


if __name__ == "__main__":
    unittest.main()
