"""Regression guards for Canvas HTML keyboard behavior that must match macOS native."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html"
RUNNER = ROOT / "run_core_tests.sh"


class HtmlNativeKeyboardParityStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HTML.read_text(encoding="utf-8")
        cls.runner = RUNNER.read_text(encoding="utf-8")
        cls.keydown = cls._slice(
            cls.source,
            "window.addEventListener('keydown',e=>{",
            "window.addEventListener('keyup',e=>",
        )
        cls.control = cls._slice(cls.source, "function control(action){", "function render(){")
        cls.move = cls._slice(cls.source, "function moveCandidate(delta){", "function moveCandidateGrid(direction){")
        cls.core = cls._slice(cls.source, "const BPMF =", "function createImeCore(payload){")
        cls.utils = cls._slice(cls.source, "const TONE_SYMBOLS=", "function keyboardPunctuation(")

    @staticmethod
    def _slice(source, start_marker, end_marker):
        start = source.find(start_marker)
        if start < 0:
            return ""
        end = source.find(end_marker, start)
        return source[start:] if end < 0 else source[start:end]

    def test_plain_f9_toggles_script_before_language_specific_routing(self):
        expected = "if(!e.metaKey&&!e.ctrlKey&&!e.altKey && e.code==='F9'){e.preventDefault();switchOutputScript();return;}"
        self.assertIn(expected, self.keydown)
        self.assertLess(self.keydown.index(expected), self.keydown.index("if(state.inputMode==='en'){"))

    def test_first_tone_helper_matches_native_trailing_bopomofo_rule(self):
        self.assertIn("const TONES = 'ˉˊˇˋ˙';", self.core)
        self.assertIn("full===bare && bare && input.startsWith(bare+'ˉ',pos)", self.source)
        self.assertGreaterEqual(self.source.count("full===bare && bare && input.startsWith(bare+'ˉ',pos)"), 2)
        self.assertIn("full===bare && bare && input.startsWith(bare+'ˉ')", self.source)
        self.assertIn("full===bare && bare && input.startsWith(bare+'ˉ',b.pos)", self.source)
        self.assertIn("const TONE_SYMBOLS=new Set(['ˉ','ˊ','ˇ','ˋ','˙']);", self.utils)
        self.assertIn("function compositionNeedsFirstTone(composition){", self.utils)
        self.assertIn("return last>='ㄅ'&&last<='ㄩ'&&!isToneSymbol(last);", self.utils)

    def test_space_matches_native_first_tone_confirm_pending_and_idle_paths(self):
        self.assertIn("if(compositionNeedsFirstTone(state.composition)){handleSymbol('ˉ');return;}", self.control)
        self.assertIn("if(state.composition){if(state.candidates.length)chooseSelectedCandidate();return;}", self.control)
        self.assertIn("if(state.pendingParts.length){stagePunctuation(' ');return;}", self.control)
        self.assertIn("state.committed+=' ';render();", self.control)
        self.assertNotIn("setToast('先按 Enter 確認組字')", self.control)

    def test_arrow_movement_clamps_instead_of_wrapping(self):
        self.assertIn("state.selected=Math.max(0,Math.min(candidates.length-1,state.selected+delta));render();", self.move)
        self.assertNotIn("%candidates.length", self.move)
        self.assertIn("const rowSize=state.specialMode?10:candidateColumns();", self.source)

    def test_full_guide_describes_real_f9_and_space_behavior(self):
        self.assertIn("直接按 <kbd>F9</kbd> 可切換繁／簡輸出", self.source)
        self.assertNotIn("用候選面板右側「繁／簡」按鈕模擬 <kbd>F9</kbd>", self.source)
        self.assertIn("未標聲調時補上第一聲 <kbd>ˉ</kbd>", self.source)
        self.assertIn("已有聲調時會選取目前候選但不立即送出", self.source)

    def test_runner_invokes_keyboard_parity_test(self):
        self.assertIn("python3 Tests/test_html_native_keyboard_parity_static.py", self.runner)


if __name__ == "__main__":
    unittest.main()
