# 逐音輸入法記憶體優化設計

## 目標
在不刪除詞庫、學習、連續組句、OpenCC、Emoji 或候選功能的前提下，降低 InputMethodKit 常駐記憶體與視窗 backing store 高水位。

## 設計
1. `ZYCandidatePanel.candidateDelegate` 改回 weak，消除 `ZYInputController -> ZYCandidatePanel -> ZYInputController` retain cycle。
2. `ZYInputController` 不在初始化時建立候選 Panel；只有候選真的需要顯示時才 lazy 建立。deactivate/close 時完整釋放 Panel。
3. 說明與清除學習子 Panel 關閉時不只 `orderOut`，也清 owner/contentView、`close` 並把 panel/view ivar 設為 nil，以釋放 backing store。下次使用再建立。
4. 候選繪圖共用 paragraph style 與常用 attributes，避免每個 cell 重複建立相同 AppKit 物件；不建立大型永久 cache。
5. 保持既有滑鼠路由、非 Modal 清除確認、候選定位、繁簡、說明內容與所有核心功能不變。

## 驗證
- 靜態回歸測試鎖住 weak delegate、lazy candidate panel、子 panel release lifecycle、繪圖共用物件。
- 跑完整 `run_core_tests.sh`、Objective-C++ linkage/panel 檢查、安裝目的地與 shell 語法檢查。
- Linux 環境不能量 macOS AppKit RSS；實際 42 MB → 新值需由使用者 Mac 活體測量確認。
