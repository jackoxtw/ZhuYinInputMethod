# 系統層輸入法安裝設計

## 目標

逐音輸入法只安裝於 `/Library/Input Methods/逐音輸入法.app`，避免同時存在系統層與使用者層副本，造成 LaunchServices 與輸入來源重複註冊。

## 範圍

- `build_and_install.command`：以管理員權限建立或更新系統層目的地；安裝前清理舊的使用者層副本與舊名稱 `逐音輸入法2.app`；LaunchServices 只註冊系統層副本。
- `uninstall.command`：以管理員權限移除系統層副本，並清理可能殘留的使用者層副本。
- `README.md`：說明系統層安裝位置及安裝、卸載時會要求管理員密碼。
- 回歸檢查：以靜態測試驗證兩個腳本的唯一正式目的地、舊副本清理與 README 說明一致。

## 不在範圍

- 不會修改輸入法的 bundle ID、輸入來源 ID 或輸入引擎程式。
- 不會自動刪除 HIToolbox 的使用者輸入來源設定；macOS 對已顯示的舊條目仍可能需要登出再登入後清除。

## 安裝流程

1. 編譯並驗證 App bundle。
2. 以 `sudo` 建立 `/Library/Input Methods`，刪除相同名稱的既有系統層 bundle，並複製新 bundle 到系統層目的地。
3. 刪除使用者層的舊 bundle，確保不會與系統層同時被註冊。
4. 反註冊建置目錄與使用者層舊 bundle；只註冊系統層 bundle。
5. 啟動系統層 bundle 並刷新相關文字輸入服務。

## 錯誤處理

腳本使用既有的 `set -euo pipefail`。使用者取消管理員驗證或系統層複製失敗時，腳本立即停止，不會繼續註冊或啟動未安裝的副本。
