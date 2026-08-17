# 單按 Shift 取消未確認注音 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 單按 Shift 切換英文時清除未確認注音，但先送出已確認中文片段。

**Architecture:** 原生版調整 `toggleLanguage:`，其是單按 Shift 與選單共用的模式切換入口；先以 `learnAndCommit:` 處理 `_pieceCount`，再清除 `_composition`／候選，最後切換模式。HTML 試用版調整 `switchInputMode()` 採相同順序，並以靜態回歸檢查保護兩端。

**Tech Stack:** Objective-C++／InputMethodKit、HTML Canvas、JavaScript、Python 靜態回歸測試。

## Global Constraints

- 未確認注音不得因單按 Shift 被選取或輸出。
- 已確認 `_pieceCount`／`pendingParts` 必須在切換英文前提交。
- `Shift + 英文字母`、`Shift + 1～0`、`Shift + A～J` 行為不可回歸。
- 單按 Shift 的 keyup 切換機制保持不變，僅改變切換當下的組字處理。
- HTML 行為需與原生版一致。

---

### Task 1: 修正 macOS 單按 Shift 切換

**Files:**
- Modify: `Tests/test_idle_space_caps_shift_static.py`
- Modify: `Platforms/macOS/App/ZYInputController.mm:276-282`

**Interfaces:**
- Consumes: `_composition`、`_candidateCount`、`_pieceCount`、`learnAndCommit:`、`showInternalState:`。
- Produces: `toggleLanguage:` 不選取未確認候選，已確認片段先輸出。

- [ ] **Step 1: 寫入失敗的回歸檢查**

在靜態測試加入 `toggleLanguage:` 區塊的檢查：

```python
toggle = controller[controller.index('- (void)toggleLanguage:'):controller.index('- (void)toggleScript:', controller.index('- (void)toggleLanguage:'))]
assert '[self chooseSelected:client]' not in toggle
assert 'if(_pieceCount)[self learnAndCommit:client];' in toggle
assert '[_composition setString:@""]' in toggle
assert '[self showInternalState:client]' in toggle
```

- [ ] **Step 2: 確認測試失敗**

Run: `python3 Tests/test_idle_space_caps_shift_static.py`

Expected: FAIL，既有 `toggleLanguage:` 仍會 `chooseSelected:`。

- [ ] **Step 3: 以最小變更調整切換順序**

將：

```objc
if(_chinese&&_composition.length&&_candidateCount)[self chooseSelected:client];
if(_chinese&&_pieceCount)[self learnAndCommit:client];
```

替換為：

```objc
if(_chinese&&_pieceCount)[self learnAndCommit:client];
if(_chinese&&(_composition.length||_candidateCount)){
    [_composition setString:@""];
    _candidateCount=0;
    _selected=0;
    [self showInternalState:client];
}
```

- [ ] **Step 4: 驗證原生版**

Run: `python3 Tests/test_idle_space_caps_shift_static.py && ./run_core_tests.sh`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add Platforms/macOS/App/ZYInputController.mm Tests/test_idle_space_caps_shift_static.py
git commit -m "fix: discard unconfirmed Zhuyin on Shift toggle"
```

### Task 2: 同步 HTML 試用版與使用者說明

**Files:**
- Modify: `Docs/Reference/台灣注音輸入法_Canvas_單檔版(20260812-065531).html:754-763`
- Modify: `Tests/test_html_shift_english_static.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `state.composition`、`state.candidates`、`state.pendingParts`、`finalizePending()`、`switchInputMode()`。
- Produces: HTML `switchInputMode()` 先完成 pending、取消 composition，後切換模式；README 說明單按 Shift 規則。

- [ ] **Step 1: 擴充失敗的 HTML 靜態測試**

加入：

```python
switch_start = html.index('function switchInputMode(){')
switch_end = html.index('function switchOutputScript(){', switch_start)
switch_block = html[switch_start:switch_end]
assert 'if(state.inputMode===\'zh\' && state.pendingParts.length) finalizePending();' in switch_block
assert "state.composition=''" in switch_block
assert 'state.candidates=[]' in switch_block
assert 'commitCandidate()' not in switch_block
```

- [ ] **Step 2: 確認測試失敗**

Run: `python3 Tests/test_html_shift_english_static.py`

Expected: FAIL，舊 `switchInputMode()` 會呼叫 `commitCandidate()`。

- [ ] **Step 3: 調整 HTML 模式切換**

將：

```javascript
if(state.inputMode==='zh' && state.composition){
  if(!commitCandidate()) return false;
}
if(state.inputMode==='zh' && state.pendingParts.length) finalizePending();
```

替換為：

```javascript
if(state.inputMode==='zh' && state.pendingParts.length) finalizePending();
if(state.inputMode==='zh' && (state.composition || state.candidates.length)){
  state.composition='';
  state.candidates=[];
  state.selected=0;
}
```

在 README 的單按 Shift 說明增加：`單按 Shift 切英文時，未確認注音會取消；已確認中文會先送出。`

- [ ] **Step 4: 執行完整驗證**

Run: `python3 Tests/test_html_shift_english_static.py && ./run_core_tests.sh && git diff --check`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add Docs/Reference/台灣注音輸入法_Canvas_單檔版\(20260812-065531\).html Tests/test_html_shift_english_static.py README.md
git commit -m "fix: align Shift toggle composition handling"
```
