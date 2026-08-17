# Shift 英文輸入取消未確認注音 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按 `Shift + 英文字母` 時取消未確認注音而不送出候選，並在原生版與 HTML 試用版維持一致。

**Architecture:** macOS `ZYInputController` 在 Shift 英文字母分支中，先保留已確認 `_pieces` 的提交，再清除未確認 `_composition`、候選與 marked text，最後插入英文。HTML 試用版在候選快捷鍵判斷之後加入相同的取消組字與英文輸入分支；兩端都不變更候選快捷鍵或單按 Shift 切換模式。

**Tech Stack:** Objective-C++／InputMethodKit、HTML Canvas、JavaScript、Python 靜態回歸測試。

## Global Constraints

- `Shift + 1～0` 與 `Shift + A～J` 必須優先作為候選快捷鍵。
- 單獨按下再放開 Shift 必須維持中英切換。
- 未確認 `_composition` 不得因 `Shift + 英文字母` 呼叫 `chooseSelected:` 或送出候選。
- 已確認 `_pieceCount` 片段仍必須先透過 `learnAndCommit:` 送出。
- Caps Lock 的既有英文大小寫規則不可改變。

---

### Task 1: 保護原生 Shift 英文輸入行為

**Files:**
- Modify: `Tests/test_idle_space_caps_shift_static.py`
- Modify: `Platforms/macOS/App/ZYInputController.mm:327-340`

**Interfaces:**
- Consumes: `_composition`、`_candidateCount`、`_pieceCount`、`showInternalState:`、`learnAndCommit:`。
- Produces: Shift 英文字母分支只提交已確認片段，未確認組字清空後再插入英文。

- [ ] **Step 1: 寫入會失敗的靜態測試**

在 `Tests/test_idle_space_caps_shift_static.py` 的 `latin_block` 檢查加入：

```python
assert '[self chooseSelected:client]' not in latin_block, \
    'Shift English must not commit an unconfirmed selected candidate'
assert '[_composition setString:@""]' in latin_block, \
    'Shift English must discard unconfirmed Zhuyin composition'
assert '[self showInternalState:client]' in latin_block, \
    'Discarding composition must also clear marked text and candidate UI'
assert 'if(_pieceCount)[self learnAndCommit:client];' in latin_block, \
    'Already confirmed pieces must still commit before Latin input'
```

- [ ] **Step 2: 確認測試目前失敗**

Run: `python3 Tests/test_idle_space_caps_shift_static.py`

Expected: FAIL，因為現有分支仍含有 `[self chooseSelected:client]`。

- [ ] **Step 3: 以最小變更取消未確認組字**

將 `Platforms/macOS/App/ZYInputController.mm` 的 Shift 英文分支中：

```objc
if(_composition.length&&_candidateCount)[self chooseSelected:client];
if(_pieceCount)[self learnAndCommit:client];
```

替換為：

```objc
if(_pieceCount)[self learnAndCommit:client];
if(_composition.length || _candidateCount) {
    [_composition setString:@""];
    _candidateCount=0;
    _selected=0;
    [self showInternalState:client];
}
```

`hadCandidates` 保留在分支前取得，確保現有 Caps Lock 大小寫邏輯不改變。

- [ ] **Step 4: 驗證原生靜態測試與完整回歸**

Run: `python3 Tests/test_idle_space_caps_shift_static.py && ./run_core_tests.sh`

Expected: PASS；候選快捷鍵、Caps Lock、核心與 macOS 靜態測試皆通過。

- [ ] **Step 5: 提交原生行為修正**

```bash
git add Platforms/macOS/App/ZYInputController.mm Tests/test_idle_space_caps_shift_static.py
git commit -m "fix: discard unconfirmed Zhuyin before Shift English"
```

### Task 2: 同步 HTML 試用版 Shift 英文行為

**Files:**
- Create: `Tests/test_html_shift_english_static.py`
- Modify: `Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html:1143-1150`

**Interfaces:**
- Consumes: `state.composition`、`state.candidates`、`state.pendingParts`、`state.pendingText`、`state.pendingQuery`、`handleEnglishChar()`。
- Produces: 中文模式的 Shift 英文字母取消 `composition` 與候選，保留已確認 pending 資料並立即以 `handleEnglishChar()` 插入英文。

- [ ] **Step 1: 建立會失敗的 HTML 靜態測試**

建立 `Tests/test_html_shift_english_static.py`：

```python
from pathlib import Path

html = Path('Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html').read_text(encoding='utf-8')
start = html.index("if(e.shiftKey && /^Key[A-J]/")
end = html.index("const zhPunct=", start)
block = html[start:end]

assert "state.composition=''" in block
assert "state.candidates=[]" in block
assert 'handleEnglishChar(e.key)' in block
print('test_html_shift_english_static: OK')
```

- [ ] **Step 2: 確認 HTML 測試目前失敗**

Run: `python3 Tests/test_html_shift_english_static.py`

Expected: FAIL，因為候選快捷鍵後尚未有 Shift 英文字母分支。

- [ ] **Step 3: 在候選快捷鍵後加入取消組字分支**

在 `Shift + A～J` 候選快捷鍵後、`candidateMode` 數字快捷鍵前加入：

```javascript
if(e.shiftKey && /^[a-z]$/i.test(e.key)){
  e.preventDefault();
  state.composition='';
  state.candidates=[];
  state.selected=0;
  state.candidateMode=false;
  handleEnglishChar(e.key);
  return;
}
```

不要清除 `pendingText`、`pendingQuery`、`pendingSegments` 或 `pendingParts`；它們代表先前已確認的片段，會保留到既有 Enter 提交流程。

- [ ] **Step 4: 驗證 HTML 與完整回歸**

Run: `python3 Tests/test_html_shift_english_static.py && ./run_core_tests.sh`

Expected: PASS；HTML 分支位於候選快捷鍵之後，且完整既有回歸均通過。

- [ ] **Step 5: 提交 HTML 同步修正**

```bash
git add Docs/Reference/台灣注音輸入法_Canvas_單檔版\(20260812-065531\).html Tests/test_html_shift_english_static.py
git commit -m "fix: align HTML Shift English composition handling"
```

### Task 3: 更新使用者說明

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: 已實作的 Shift 英文行為。
- Produces: 使用者可理解的快捷鍵說明，不暗示未確認注音會被送出。

- [ ] **Step 1: 加入說明靜態檢查**

在 `Tests/test_shortcuts_static.py` 加入：

```python
readme = (root / 'README.md').read_text(encoding='utf-8')
assert '未確認注音會取消，不會送出候選' in readme
```

- [ ] **Step 2: 確認說明檢查目前失敗**

Run: `python3 Tests/test_shortcuts_static.py`

Expected: FAIL，因為 README 尚未說明取消規則。

- [ ] **Step 3: 更新 README 快捷鍵表格**

將 `Shift + 英文字母` 的說明更新為：

```markdown
| `Shift + 英文字母` | 已確認中文會先送出；未確認注音會取消，不會送出候選，接著輸入英文；閒置時 Caps Lock 關＝小寫，開＝大寫 |
```

- [ ] **Step 4: 執行最終驗證**

Run: `./run_core_tests.sh && git diff --check`

Expected: PASS，且沒有空白或格式錯誤。

- [ ] **Step 5: 提交說明更新**

```bash
git add README.md Tests/test_shortcuts_static.py
git commit -m "docs: clarify Shift English composition behavior"
```
