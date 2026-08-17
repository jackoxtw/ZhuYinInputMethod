# HTML 特殊候選與完整使用說明 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 讓 Canvas HTML 試用版提供與 macOS 原生版一致的反引號 Emoji、單引號中文標點特殊候選，並在畫面底部提供常駐完整使用說明。

**Architecture:** 在既有 `state.candidates` 之外加入明確的 `specialMode` 狀態；一般注音候選仍由查詞函式產生，特殊候選則由與原生相同的常數資料提供。所有候選導覽、選取與滑鼠命中沿用既有畫面管線，透過候選來源、每頁大小與選取提交分支處理差異。頁尾說明用 Canvas 之後的語意 HTML 區塊呈現，因此可隨網頁正常捲動且不受 Canvas 尺寸限制。

**Tech Stack:** 單檔 HTML、Canvas 2D、原生 JavaScript、Python 3 靜態回歸測試、POSIX shell 測試入口。

## Global Constraints

- 僅修改 HTML 試用版及其測試；不得修改 macOS 原生 Emoji／標點實作。
- Emoji、中文標點資料與原生 `ZYInputController.mm` 完全一致；特殊候選每頁固定 50 筆，一般候選維持每頁 20 筆。
- 開啟特殊候選不得清除 `composition`、`pendingParts` 或其他已確認片段。
- 特殊候選必須支援方向鍵、Page Up／Down、Home／End、Enter、Space、滑鼠及 Esc；Shift 候選快捷鍵、中英切換、Caps Lock 與 Shift 英文保護不得退化。
- 頁尾完整使用說明必須常駐、可捲動閱讀、與目前 Shift 取消未確認注音的行為一致；不可用彈出視窗替代。
- 每個修改任務先寫會失敗的測試，再寫最小實作；完成後執行 `./run_core_tests.sh`。

---

## File Structure

- `Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html`：新增特殊候選常數、狀態與導覽／選取分支；將 Canvas 候選面板繪製為一般或特殊候選；新增 Canvas 之後的完整使用說明 HTML 區塊與樣式。
- `Tests/test_html_special_candidates_static.py`：檢查特殊資料、開關行為、輸入／選取／Esc 路徑、每頁 50 筆，以及底部說明的必要文案。
- `run_core_tests.sh`：將上述 HTML 回歸測試加入既有 Python 靜態測試序列。

### Task 1: 特殊候選狀態、資料與鍵盤行為

**Files:**
- Create: `Tests/test_html_special_candidates_static.py`
- Modify: `Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html:709-986,1118-1188`
- Modify: `run_core_tests.sh:20-65`

**Interfaces:**
- Consumes: `state.composition`, `state.pendingParts`, `state.candidates`, `state.selected`, `refreshCandidates()`, `stagePunctuation()`, `commitCandidate()`, `pageCandidate()`.
- Produces: `SPECIAL_CANDIDATES`, `openSpecialCandidates(mode)`, `closeSpecialCandidates()`, `specialCandidates()`, `activeCandidates()`, `candidatePageSize()`, and `chooseSelectedCandidate()` for Task 2 to render and select either source.

- [ ] **Step 1: Write failing tests for special-candidate semantics**

Create `Tests/test_html_special_candidates_static.py` with `unittest` tests that require the following source-level contracts:

```python
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
    self.assertIn("if(e.code==='Backquote'){e.preventDefault();toggleSpecialCandidates('emoji');return;}", self.keydown_block)
    self.assertIn("if(e.code==='Quote'){e.preventDefault();toggleSpecialCandidates('punctuation');return;}", self.keydown_block)
    self.assertIn("if(state.specialMode){closeSpecialCandidates();return;}", self.escape_block)
    self.assertIn("if(state.specialMode)return chooseSelectedCandidate();", self.space_block)
    self.assertIn("if(state.specialMode)return chooseSelectedCandidate();", self.enter_block)
```

Also assert that the Zhuyin input path calls `closeSpecialCandidates()` before `handleSymbol(sym)`, and that this test file is invoked by `run_core_tests.sh`.

- [ ] **Step 2: Run the new test and verify it fails**

Run: `python3 Tests/test_html_special_candidates_static.py`

Expected: FAIL because special constants, `specialMode`, and the keyboard routing do not exist yet.

- [ ] **Step 3: Add special data and source-agnostic candidate helpers**

In the HTML script, immediately before `state`, define `SPECIAL_CANDIDATES` with the exact Emoji and punctuation arrays from `Platforms/macOS/App/ZYInputController.mm:17-34`. Add `specialMode:null` to `state`.

Add these helpers next to `refreshCandidates()`:

```javascript
function specialCandidates(){ return state.specialMode ? SPECIAL_CANDIDATES[state.specialMode] : []; }
function activeCandidates(){ return state.specialMode ? specialCandidates() : state.candidates; }
function candidatePageSize(){ return state.specialMode ? 50 : 20; }
function openSpecialCandidates(mode){
  if(!SPECIAL_CANDIDATES[mode]?.length) return false;
  state.specialMode=mode;state.selected=0;state.candidateMode=false;render();return true;
}
function closeSpecialCandidates(){
  if(!state.specialMode) return false;
  state.specialMode=null;refreshCandidates();return true;
}
function toggleSpecialCandidates(mode){
  return state.specialMode===mode ? closeSpecialCandidates() : openSpecialCandidates(mode);
}
```

Make `pageStart`, `commitSlot`, `moveCandidate`, `moveCandidateGrid`, `pageCandidate`, and `edgeCandidate` read `activeCandidates()` and `candidatePageSize()` rather than hard-coding `state.candidates` and `state.visibleCandidates`. Keep the existing wrap behavior for arrow movement and clamped page movement.

Add `chooseSelectedCandidate()`:

```javascript
function chooseSelectedCandidate(){
  if(!state.specialMode) return commitCandidate(state.selected);
  const item=specialCandidates()[state.selected];
  if(!item) return false;
  state.specialMode=null;state.selected=0;stagePunctuation(item);refreshCandidates();return true;
}
```

In `commitSlot`, select via `activeCandidates()` and then call `chooseSelectedCandidate()`. This preserves the existing Shift and numpad candidate shortcut routing for both kinds of candidate.

- [ ] **Step 4: Route special keys and preserve all composition semantics**

In Chinese-mode `keydown`, after the existing Shift candidate shortcut checks and before `keyboardPunctuation`, add exact physical-key routing:

```javascript
if(!e.shiftKey && e.code==='Backquote'){e.preventDefault();toggleSpecialCandidates('emoji');return;}
if(!e.shiftKey && e.code==='Quote'){e.preventDefault();toggleSpecialCandidates('punctuation');return;}
```

Do not move the existing Shift+1–0/A–J checks: they must retain higher priority than Shift-English handling. Keep the existing Shift-English path unchanged other than calling `closeSpecialCandidates()` first when a special panel is open, then retaining its existing pending-finalize, composition-discard, and English insertion sequence.

For `Space` and `Enter`, branch before regular composition handling:

```javascript
if(state.specialMode)return chooseSelectedCandidate();
```

For `Escape`, close special candidates first, before the existing clear-composition and clear-pending branches. For Backspace, close special candidates first and return. Immediately before the final `handleSymbol(sym)` call, close a special panel so the newly typed Zhuyin restores ordinary candidates. Do not clear composition or pending parts in any special-panel open/close path.

- [ ] **Step 5: Run the focused tests and verify they pass**

Run: `python3 Tests/test_html_special_candidates_static.py && python3 Tests/test_html_shift_english_static.py && python3 Tests/test_html_native_parity_static.py`

Expected: all pass; this proves special behavior was added without changing the Shift/candidate parity contracts.

- [ ] **Step 6: Add the regression to the complete runner and commit**

Insert `python3 Tests/test_html_special_candidates_static.py` directly after `test_html_shift_english_static.py` in `run_core_tests.sh`.

Run: `./run_core_tests.sh`

Expected: exit code 0 and the existing complete core/static suite passes.

Commit:

```bash
git add Docs/Reference/台灣注音輸入法_Canvas_單檔版\(20260812-065531\).html Tests/test_html_special_candidates_static.py run_core_tests.sh
git commit -m "feat: add HTML special candidates"
```

### Task 2: 特殊候選 Canvas 呈現、滑鼠選取與頁底完整說明

**Files:**
- Modify: `Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html:1-20,998-1115`
- Modify: `Tests/test_html_special_candidates_static.py`

**Interfaces:**
- Consumes: Task 1 `state.specialMode`, `activeCandidates()`, `candidatePageSize()`, `chooseSelectedCandidate()`, `closeSpecialCandidates()`.
- Produces: special panel label and 50-item grid, mouse selection through `chooseSelectedCandidate`, plus an accessible permanent `<section class="full-guide">` following `#imeCanvas`.

- [ ] **Step 1: Extend the failing test for canvas and guide contracts**

Add these tests to `Tests/test_html_special_candidates_static.py`:

```python
def test_canvas_renders_special_source_and_mouse_uses_special_selection(self):
    self.assertIn("const candidates=activeCandidates();", self.render_block)
    self.assertIn("const visible=candidatePageSize();", self.render_block)
    self.assertIn("state.specialMode==='emoji'?'Emoji 候選':'中文標點候選'", self.render_block)
    self.assertIn("else chooseSelectedCandidate(hit.index);", self.pointer_block)

def test_bottom_guide_is_permanent_and_documents_current_behavior(self):
    self.assertIn('<section class="full-guide" aria-labelledby="full-guide-title">', self.source)
    self.assertGreater(self.source.index('<section class="full-guide"'), self.source.index('<canvas id="imeCanvas"'))
    for phrase in ['Shift 英文字母', '取消未確認注音', '反引號 `', "單引號 '", 'F9', 'Option', '僅保存在本機']:
        self.assertIn(phrase, self.source)
```

The test must also require the replacement top note to say “取消未確認注音”, preventing the old incorrect “送出未確認中文” instruction from returning.

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `python3 Tests/test_html_special_candidates_static.py`

Expected: FAIL because the Canvas still hard-codes `state.candidates`, mouse selection still calls `commitCandidate`, and no page-bottom guide exists.

- [ ] **Step 3: Render 50 special candidates without clipping existing controls**

In `render()`, replace the candidate loop source with:

```javascript
const candidates=activeCandidates();
const visible=candidatePageSize();
const columns=state.specialMode?10:candidateColumns();
const rows=Math.ceil(visible/columns);
```

Use `candidates[abs]` for chips. In special mode, display each candidate string directly (`const word=state.specialMode ? c : c.word`), show a panel label `state.specialMode==='emoji'?'Emoji 候選':'中文標點候選'`, and do not show learning deletion labels. Only draw keyboard shortcut labels for slots 0–19; leave slots 20–49 without shortcut labels because they have no corresponding Shift key combination.

Set the canvas height in `resize()` to `w<560?1060:1145`, which reserves the additional three candidate rows needed by a 50-item, 10-column special grid while keeping all existing keyboard and control buttons visible. Update candidate status text to tell the user that Esc closes the current Emoji or punctuation panel; normal no-candidate copy remains unchanged.

Use `activeCandidates().length` in the candidate swipe condition. In `pointerup`, keep the Option deletion branch only for ordinary candidates, otherwise call `chooseSelectedCandidate(hit.index)` after setting `state.selected=hit.index`; this makes clicking an Emoji/punctuation insert it as a staged punctuation piece and restore normal candidates.

Update the in-canvas quick-help strings and bottom status line to include `` ` Emoji`` and `' 標點` when Chinese mode is active. Update the top `.note` text to accurately say that Shift-English cancels unconfirmed Zhuyin, and link readers to the bottom full guide.

- [ ] **Step 4: Add permanent semantic page-bottom guide and styles**

Add compact responsive CSS in `<head>` for `.full-guide`, `.full-guide h2`, `.full-guide h3`, `.full-guide ul`, and `.full-guide kbd`, matching the current pale Canvas page theme and allowing normal document scroll. Directly after the canvas/top note, add:

```html
<section class="full-guide" aria-labelledby="full-guide-title">
  <h2 id="full-guide-title">完整使用說明</h2>
  <h3>注音與候選</h3>
  <ul>…</ul>
  <h3>中英切換與快捷鍵</h3>
  <ul>…</ul>
  <h3>Emoji、標點與個人學習</h3>
  <ul>…</ul>
</section>
```

Fill the lists with exact current behavior: typing Zhuyin, arrows and page movement, Enter/Space/mouse selection; a single Shift mode toggle; Shift+English committing confirmed pieces but cancelling unconfirmed Zhuyin; Shift+1–0/A–J and Caps Lock; backquote Emoji, quote Chinese punctuation, Esc close; F9 Traditional/Simplified final output; Option only deletes learned candidates; and learning remains in browser local storage only. Do not mention that a single Shift submits unfinished Chinese.

- [ ] **Step 5: Run complete verification and inspect page structure**

Run:

```bash
python3 Tests/test_html_special_candidates_static.py
python3 Tests/test_html_shift_english_static.py
python3 Tests/test_html_native_parity_static.py
./run_core_tests.sh
git diff --check
```

Expected: every command exits 0. Manually open the local HTML in the browser and verify a 50-item special panel does not cover keyboard/control buttons, the bottom “完整使用說明” is below the Canvas and scrolls normally, and pressing Esc returns the previously entered Zhuyin candidates.

- [ ] **Step 6: Commit the presentation and documentation behavior**

```bash
git add Docs/Reference/台灣注音輸入法_Canvas_單檔版\(20260812-065531\).html Tests/test_html_special_candidates_static.py
git commit -m "docs: add HTML input guide"
```

## Self-Review

1. **Spec coverage:** Task 1 covers exact special data, open/toggle/close preservation, every requested keyboard selector and automatic close on Zhuyin; Task 2 covers 50-item presentation, mouse selection, no Option deletion for special items, and all required bottom-guide topics. macOS remains untouched.
2. **Placeholder scan:** No TBD/TODO or generic testing instruction remains; each change names its files, functions, expected test result, and commit.
3. **Type consistency:** `state.specialMode` is `null | 'emoji' | 'punctuation'`; `SPECIAL_CANDIDATES` maps those keys to string arrays; `activeCandidates()` returns either string candidates or existing candidate objects, and Task 2 explicitly branches display and selection by `specialMode`.
