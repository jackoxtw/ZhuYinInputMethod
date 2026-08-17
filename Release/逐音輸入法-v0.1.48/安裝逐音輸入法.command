#!/bin/bash
set -euo pipefail

if [[ -t 1 && "${TERM:-dumb}" != "dumb" ]]; then
  C_BLUE=$'\033[1;34m'; C_CYAN=$'\033[0;36m'; C_GREEN=$'\033[1;32m'
  C_YELLOW=$'\033[1;33m'; C_RED=$'\033[1;31m'; C_RESET=$'\033[0m'
else
  C_BLUE=''; C_CYAN=''; C_GREEN=''; C_YELLOW=''; C_RED=''; C_RESET=''
fi
step(){ printf '\n%b【%s】%b\n' "$C_BLUE" "$1" "$C_RESET"; }
info(){ printf '%b  %s%b\n' "$C_CYAN" "$1" "$C_RESET"; }
success(){ printf '%b  ✓ %s%b\n' "$C_GREEN" "$1" "$C_RESET"; }
warn(){ printf '%b  ⚠ %s%b\n' "$C_YELLOW" "$1" "$C_RESET"; }
fail(){ printf '%b  ✗ %s%b\n' "$C_RED" "$1" "$C_RESET" >&2; }

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$SCRIPT_DIR/逐音輸入法.app"
DEST="/Library/Input Methods/逐音輸入法.app"
LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
STAGE_DIR="$(mktemp -d /private/tmp/zhuyin-install.XXXXXX)"
STAGED_APP="$STAGE_DIR/逐音輸入法.app"
trap 'rm -rf "$STAGE_DIR"' EXIT

step "1/3 檢查 Release 內容"
if [[ ! -d "$APP" ]]; then
  fail "找不到『逐音輸入法.app』。請勿單獨移動本安裝器，請從完整 Release 目錄執行。"
  read -r -p "按 Enter 關閉。"
  exit 2
fi
success "已找到已編譯的逐音輸入法.app"

step "2/3 驗證 App 完整性"
info "正在移除 Finder 附加資訊並驗證 Release…"
ditto "$APP" "$STAGED_APP"
xattr -cr "$STAGED_APP"
if ! /usr/bin/codesign --verify --deep --strict "$STAGED_APP"; then
  fail "App 完整性驗證失敗，請重新下載完整 Release。"
  read -r -p "按 Enter 關閉。"
  exit 3
fi
success "App 完整性驗證通過"

step "3/3 安裝到系統輸入法目錄"
warn "macOS 即將要求管理員密碼；輸入時不會顯示字元，這是正常的。"
sudo -v

if [[ -x "$LSREGISTER" ]]; then
  "$LSREGISTER" -u "$DEST" 2>/dev/null || true
fi
sudo rm -rf "$DEST"
sudo mkdir -p "/Library/Input Methods"
sudo ditto "$STAGED_APP" "$DEST"
sudo chown -R root:wheel "$DEST"
/usr/bin/codesign --verify --deep --strict "$DEST"
success "已安裝並驗證系統輸入法"

if [[ -x "$LSREGISTER" ]]; then
  "$LSREGISTER" -f "$DEST" 2>/dev/null || true
fi

killall ZhuYinInputMethod 逐音輸入法 逐音輸入法2 2>/dev/null || true
open "$DEST" || true
open "x-apple.systempreferences:com.apple.Keyboard-Settings.extension" 2>/dev/null || true

echo
success "安裝完成"
info "請在『鍵盤 → 文字輸入 → 編輯 → +』加入『逐音輸入法』。"
warn "若 macOS 顯示無法驗證開發者，請到『隱私權與安全性』按『仍要打開』後重試。"
read -r -p "按 Enter 關閉。"
