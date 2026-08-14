# 跨平台目錄與共用核心設計

## 目標

將專案整理為 macOS 與未來 Windows 可共同使用同一套查詞、組句、學習、繁簡轉換與二進位資料；兩端僅各自實作作業系統輸入法介面與發行流程。

## 目錄責任

```text
Shared/
  Core/          C99：詞典、引擎、組句、學習、繁簡轉換
  Resources/     dictionary.bin、t2s.bin、品牌詞與授權資料
  Tools/         產生／修復共用二進位資料的 Python 工具
  Tests/         可在 macOS 與 Windows 執行的核心測試

Platforms/
  macOS/
    App/         InputMethodKit、AppKit 候選窗、游標定位、macOS Runtime bridge
    Packaging/   .command、一般使用者說明與 Release 組裝
    scripts/     macOS 編譯、安裝、解除安裝
  Windows/
    Ime/         TSF Text Service、候選 UI、Windows Runtime bridge
    Installer/   Windows 安裝包設定
    scripts/     CMake／Visual Studio 建置命令
```

`Docs/`、`Release/`、根目錄 README 與跨平台 CMake 設定維持在專案根目錄。

## 共用邊界

- `Shared/Core` 必須維持 C99，只可依賴標準 C、專案標頭與 `Shared/Resources` 的二進位資料格式。
- 共用 API 使用 C 標頭與固定寬度型別；不得引入 Cocoa、InputMethodKit、Windows SDK、COM、Objective-C 或 C++ 類別。
- `dictionary.bin`、`t2s.bin`、學習檔格式與候選資料結構為兩端唯一來源。相同輸入與相同學習資料必須回傳相同候選順序。
- macOS Runtime bridge 和 Windows Runtime bridge 都只能將平台鍵盤事件轉成共用 Core 輸入、把候選結果顯示為各自 UI，並將確認文字交給各自系統。

## 平台實作

- macOS 延續 InputMethodKit、Objective-C++ 與現有非搶焦點候選視窗。
- Windows 使用 C++17 與 Microsoft Text Services Framework（TSF）；不複製 Core 演算法或詞庫資料。
- Windows 初期只建立可編譯的 TSF／CMake 骨架與共用 Core 連結檢查，不在這次整理中宣稱完成 Windows 可安裝輸入法。

## 驗證

- 既有 Core C 測試改由 `Shared/Tests` 使用同一組來源編譯。
- 新增跨平台靜態檢查：Shared 不得引用平台框架；兩個平台建置設定都要連結 Shared Core。
- macOS Release、安裝器、簽章與 ZIP 驗證需維持可用。
- Windows CI 或 Windows 本機建置會編譯 Shared Core 與 TSF 骨架；未具 Windows 工具鏈的 macOS 不應嘗試編譯 Windows 專案。
