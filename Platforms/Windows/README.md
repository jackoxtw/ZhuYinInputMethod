# Windows 版本（TSF 骨架）

這個目錄是 Windows 原生輸入法的起點，目標平台是 Windows 10／11、Visual Studio 2022 與 Windows SDK。它**尚未**是可安裝的 Windows 輸入法，也沒有 TSF COM 註冊、候選視窗或安裝器。

`Ime/ZhuyinTextService.*` 的 `ZhuyinWindowsCoreBridge` 只負責呼叫共用 C99 核心：開啟 `dictionary.bin`／`t2s.bin`、查候選、記錄選字學習和重設學習狀態。它不擁有視窗或 TSF 物件，因此候選排序與資料格式會和 macOS 共用。

未來應在獨立 TSF adapter 中處理 `ITfTextInputProcessor`、composition、候選 UI、使用者設定與 DLL 註冊，並把查詞和學習委派給這個 bridge；不要把演算法複製到 Windows 專屬程式碼。

在 Windows 開發機執行：

```powershell
cmake -S Platforms/Windows -B build/windows -G "Visual Studio 17 2022" -A x64
cmake --build build/windows --config Release
```

執行期資源請從 `Shared/Resources/` 複製到 DLL 旁或安裝位置，且維持原始檔名與二進位格式。
