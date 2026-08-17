"""Regression guards for HTML special candidate behavior."""

from pathlib import Path
import unittest


HTML = Path(__file__).parents[1] / "Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html"
RUNNER = Path(__file__).parents[1] / "run_core_tests.sh"


class HtmlSpecialCandidatesStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HTML.read_text(encoding="utf-8")
        cls.runner = RUNNER.read_text(encoding="utf-8")

        cls.open_special_block = cls.slice_between(
            cls.source,
            "function openSpecialCandidates(mode){",
            "function closeSpecialCandidates(){",
        )
        cls.close_special_block = cls.slice_between(
            cls.source,
            "function closeSpecialCandidates(){",
            "function toggleSpecialCandidates(mode){",
        )
        cls.keydown_block = cls.slice_between(
            cls.source,
            "window.addEventListener('keydown',e=>{",
            "window.addEventListener('keyup',e=>",
        )
        cls.escape_block = cls.slice_between(
            cls.keydown_block,
            "if(e.key==='Escape'){",
            "const sym=mapPhysicalKey(e.key);",
            after="const zhPunct=",
        )
        cls.space_block = cls.slice_between(
            cls.keydown_block,
            "if(e.key===' '){",
            "if(e.key==='Enter'){",
            after="const zhPunct=",
        )
        cls.enter_block = cls.slice_between(
            cls.keydown_block,
            "if(e.key==='Enter'){",
            "if(e.key==='ArrowLeft'){",
            after="const zhPunct=",
        )
        cls.render_block = cls.slice_between(
            cls.source,
            "function render(){",
            "function resize(){",
        )
        cls.pointer_block = cls.slice_between(
            cls.source,
            "canvas.addEventListener('pointerup',e=>{",
            "canvas.addEventListener('contextmenu',e=>",
        )
        cls.choose_selected_block = cls.slice_between(
            cls.source,
            "function chooseSelectedCandidate(absIndex=state.selected){",
            "function commitCandidate(absIndex=state.selected){",
        )
        cls.move_candidate_grid_block = cls.slice_between(
            cls.source,
            "function moveCandidateGrid(direction){",
            "function pageCandidate(delta){",
        )

    @staticmethod
    def slice_between(source, start_marker, end_marker, after=None):
        search_start = source.find(after) if after else 0
        if search_start < 0:
            search_start = 0
        start = source.find(start_marker, search_start)
        if start < 0:
            return ""
        end = source.find(end_marker, start)
        if end < 0:
            return source[start:]
        return source[start:end]

    def test_special_data_matches_native_and_uses_fifty_item_pages(self):
        self.assertIn("emoji:[\"😀\",\"😃\",\"😄\"", self.source)
        self.assertIn("punctuation:[\"，\",\"。\",\"、\",\"？\",\"！\"", self.source)
        self.assertIn("function candidatePageSize(){ return state.specialMode ? 50 : 20; }", self.source)

    def test_special_open_close_preserves_composition_and_pending_parts(self):
        self.assertIn("function openSpecialCandidates(mode){", self.source)
        self.assertIn("state.specialMode=mode", self.source)
        self.assertNotIn("state.composition=''", self.open_special_block)
        self.assertNotIn("state.pendingParts=[]", self.open_special_block)
        self.assertIn("function closeSpecialCandidates(){", self.source)
        self.assertIn("state.specialMode=null;refreshCandidates();", self.source)

    def test_keys_open_toggle_and_select_special_candidates(self):
        guarded_backquote = "if(!e.shiftKey && e.code==='Backquote'){e.preventDefault();toggleSpecialCandidates('emoji');return;}"
        guarded_quote = "if(!e.shiftKey && e.code==='Quote'){e.preventDefault();toggleSpecialCandidates('punctuation');return;}"
        zh_punct = "const zhPunct=keyboardPunctuation('zh',e.code,e.shiftKey,state.candidates.length>0);"
        self.assertIn(
            guarded_backquote,
            self.keydown_block,
        )
        self.assertIn(
            guarded_quote,
            self.keydown_block,
        )
        self.assertNotIn(
            "if(e.code==='Backquote'){e.preventDefault();toggleSpecialCandidates('emoji');return;}",
            self.keydown_block,
        )
        self.assertNotIn(
            "if(e.code==='Quote'){e.preventDefault();toggleSpecialCandidates('punctuation');return;}",
            self.keydown_block,
        )
        self.assertIn(zh_punct, self.keydown_block)
        self.assertLess(self.keydown_block.index(guarded_backquote), self.keydown_block.index(zh_punct))
        self.assertLess(self.keydown_block.index(guarded_quote), self.keydown_block.index(zh_punct))
        self.assertIn("if(state.specialMode){closeSpecialCandidates();return;}", self.escape_block)
        self.assertIn("if(state.specialMode)return chooseSelectedCandidate();", self.space_block)
        self.assertIn("if(state.specialMode)return chooseSelectedCandidate();", self.enter_block)

    def test_zhuyin_input_closes_special_candidates_before_symbol_handling(self):
        self.assertIn(
            "if(sym){e.preventDefault();closeSpecialCandidates();handleSymbol(sym);}",
            self.keydown_block,
        )

    def test_canvas_renders_special_source_and_mouse_uses_special_selection(self):
        self.assertIn("const candidates=activeCandidates();", self.render_block)
        self.assertIn("const visible=candidatePageSize();", self.render_block)
        self.assertIn("state.specialMode==='emoji'?'Emoji 候選':'中文標點候選'", self.render_block)
        self.assertIn("else chooseSelectedCandidate(hit.index);", self.pointer_block)

    def test_special_grid_vertical_navigation_uses_ten_slots_only_in_special_mode(self):
        self.assertIn(
            "const rowSize=state.specialMode?10:Math.max(1,Math.floor(candidatePageSize()/2));",
            self.move_candidate_grid_block,
        )
        self.assertNotIn(
            "const rowSize=Math.max(1,Math.floor(candidatePageSize()/2));",
            self.move_candidate_grid_block,
        )

    def test_special_selection_retries_punctuation_staging_and_restores_panel_on_failure(self):
        self.assertIn("const previousMode=state.specialMode;", self.choose_selected_block)
        self.assertIn("let previousComposition='';", self.choose_selected_block)
        self.assertIn(
            "while(!staged && state.composition && state.composition!==previousComposition){",
            self.choose_selected_block,
        )
        self.assertIn(
            "if(!staged){state.specialMode=previousMode;state.selected=absIndex;render();return false;}",
            self.choose_selected_block,
        )
        self.assertNotIn(
            "state.specialMode=null;state.selected=0;stagePunctuation(item);refreshCandidates();return true;",
            self.choose_selected_block,
        )

    def test_bottom_guide_is_permanent_and_documents_current_behavior(self):
        self.assertIn('<section class="full-guide" aria-labelledby="full-guide-title">', self.source)
        self.assertGreater(self.source.index('<section class="full-guide"'), self.source.index('<canvas id="imeCanvas"'))
        for phrase in ['Shift 英文字母', '取消未確認注音', '反引號 `', "單引號 '", 'F9', 'Option', '僅保存在本機']:
            self.assertIn(phrase, self.source)
        self.assertIn("會先送出已確認 pending 片段，再清除未確認 composition／一般候選並切換", self.source)
        self.assertIn("同樣保留已確認、取消未確認並直接輸入英文", self.source)
        self.assertIn("取消未確認注音", self.source)
        self.assertNotIn("送出未確認中文", self.source)
        self.assertNotIn("單按 <b>Shift</b> 只切換中／英輸入", self.source)
        self.assertNotIn("單按 <kbd>Shift</kbd> 只切換中英模式", self.source)

    def test_runner_invokes_special_candidate_static_test(self):
        self.assertIn("python3 Tests/test_html_special_candidates_static.py", self.runner)


if __name__ == "__main__":
    unittest.main()
