#!/bin/bash
set -euo pipefail

# Semantic terminal colors. Disable automatically when stdout is not an interactive TTY.
if [[ -t 1 && "${TERM:-dumb}" != "dumb" ]]; then
  C_BLUE=$'\033[1;34m'
  C_CYAN=$'\033[0;36m'
  C_GREEN=$'\033[1;32m'
  C_YELLOW=$'\033[1;33m'
  C_RED=$'\033[1;31m'
  C_MAGENTA=$'\033[1;35m'
  C_DIM=$'\033[2m'
  C_RESET=$'\033[0m'
else
  C_BLUE=''; C_CYAN=''; C_GREEN=''; C_YELLOW=''; C_RED=''; C_MAGENTA=''; C_DIM=''; C_RESET=''
fi
step(){ printf '\n%b【%s】%b\n' "$C_BLUE" "$1" "$C_RESET"; }
info(){ printf '%b  %s%b\n' "$C_CYAN" "$1" "$C_RESET"; }
success(){ printf '%b  ✓ %s%b\n' "$C_GREEN" "$1" "$C_RESET"; }
warn(){ printf '%b  ⚠ %s%b\n' "$C_YELLOW" "$1" "$C_RESET"; }
fail(){ printf '%b  ✗ %s%b\n' "$C_RED" "$1" "$C_RESET" >&2; }
notice(){ printf '%b  %s%b\n' "$C_MAGENTA" "$1" "$C_RESET"; }
meta(){ printf '%b  %s%b\n' "$C_DIM" "$1" "$C_RESET"; }
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
step "1/7 檢查編譯環境"
if [[ "$(uname -s)" != "Darwin" ]]; then
  fail "此腳本只能在 macOS 執行。"
  exit 2
fi
XCRUN="$(xcrun -f clang 2>/dev/null || true)"
if [[ -z "$XCRUN" ]]; then
  fail "找不到 Xcode Command Line Tools。請先執行：xcode-select --install"
  exit 3
fi
ARCH="$(uname -m)"
success "Xcode Command Line Tools 可用"
meta "架構：$ARCH"
meta "clang：$XCRUN"
# Desktop/iCloud 等檔案提供者會向 .app 加入 FinderInfo，導致 codesign 失敗。
BUILD="/private/tmp/zhu-yin-input-method-native-$ARCH"
# v0.1.7 -> v0.1.8: 複製 InfoPlist.strings 語系資源，清理中間構建 App 的 LaunchServices 註冊，修正重複與 Identifier 顯示問題
APP="$BUILD/逐音輸入法.app"
CONTENTS="$APP/Contents"
MACOS="$CONTENTS/MacOS"
RES="$CONTENTS/Resources"
OBJ="$BUILD/obj"
ICON_SOURCE="$PWD/icon/icon.png"
ICONSET="$BUILD/AppIcon.iconset"
ICON_ICNS="$BUILD/AppIcon.icns"
rm -rf "$APP" "$OBJ"
mkdir -p "$MACOS" "$RES" "$OBJ"
cp App/Info.plist "$CONTENTS/Info.plist"

# Build a Taiwan-pronunciation overlay without changing legacy word IDs.
step "2/7 更新台灣注音詞庫"
info "檢查 libchewing-data 台灣注音／多音字資料…"
# The ZIP already contains a core repaired dictionary; when network + Python are available,
# refresh all single-character readings from libchewing-data and preserve every polyphone.
DICT_FOR_BUILD="$PWD/Resources/dictionary.bin"
PYTHON3="$(command -v python3 2>/dev/null || true)"
TAIWAN_CACHE_DIR="$HOME/Library/Caches/ZhuYinInputMethod"
TAIWAN_CACHE="$TAIWAN_CACHE_DIR/libchewing-word.csv"
TAIWAN_TMP="$BUILD/dictionary.taiwan.bin"
TAIWAN_URL="https://raw.githubusercontent.com/chewing/libchewing-data/main/dict/chewing/word.csv"
if [[ -n "$PYTHON3" ]]; then
  mkdir -p "$TAIWAN_CACHE_DIR"
  if /usr/bin/curl -L --fail --silent --show-error --connect-timeout 8 --max-time 30 \
      "$TAIWAN_URL" -o "$TAIWAN_CACHE.download"; then
    mv "$TAIWAN_CACHE.download" "$TAIWAN_CACHE"
  else
    rm -f "$TAIWAN_CACHE.download"
  fi
  if [[ -f "$TAIWAN_CACHE" ]] && "$PYTHON3" Tools/repair_dictionary_taiwan.py \
      Resources/dictionary.bin "$TAIWAN_CACHE" "$TAIWAN_TMP" --require-full; then
    DICT_FOR_BUILD="$TAIWAN_TMP"
    success "已套用 libchewing-data 完整台灣注音／多音字讀音"
  else
    warn "無法取得或驗證完整 libchewing-data，改用 ZIP 內建台灣核心修正版詞庫。"
  fi
else
  warn "找不到 python3，改用 ZIP 內建台灣核心修正版詞庫。"
fi

# Re-apply built-in project words after any Taiwan reading overlay. The bundled
# fallback dictionary already contains them, so systems without Python still
# keep the same brand vocabulary.
BRAND_TMP="$BUILD/dictionary.brand.bin"
if [[ -n "$PYTHON3" ]] && "$PYTHON3" Tools/inject_dictionary_words.py \
    "$DICT_FOR_BUILD" Resources/brand_words.csv "$BRAND_TMP"; then
  DICT_FOR_BUILD="$BRAND_TMP"
  success "已套用逐音輸入法內建品牌詞"
else
  [[ -n "$PYTHON3" ]] && warn "品牌詞重建失敗，沿用 ZIP 內建品牌詞庫。"
fi
cp "$DICT_FOR_BUILD" "$RES/dictionary.bin"

# Build a complete Taiwan Traditional -> Simplified converter from the exact
step "3/7 建立簡體轉換資料"
info "檢查 OpenCC 1.3.1 台灣正體→簡體 tw2s 規則…"
# OpenCC 1.3.1 tw2s source dictionaries. Runtime still uses our compact ZYT2S1
# binary, so the installed input method has no Python/OpenCC/network dependency.
T2S_FOR_BUILD="$PWD/Resources/t2s.bin"
OPENCC_TAG="ver.1.3.1"
OPENCC_CACHE_DIR="$HOME/Library/Caches/ZhuYinInputMethod/opencc-$OPENCC_TAG"
OPENCC_BASE_URL="https://raw.githubusercontent.com/BYVoid/OpenCC/$OPENCC_TAG/data/dictionary"
OPENCC_TS_CHARS="$OPENCC_CACHE_DIR/TSCharacters.txt"
OPENCC_TS_PHRASES="$OPENCC_CACHE_DIR/TSPhrases.txt"
OPENCC_TW_VARIANTS="$OPENCC_CACHE_DIR/TWVariants.txt"
OPENCC_TW_REV_PHRASES="$OPENCC_CACHE_DIR/TWVariantsRevPhrases.txt"
OPENCC_T2S_TMP="$BUILD/t2s.opencc.bin"

if [[ -n "$PYTHON3" ]]; then
  mkdir -p "$OPENCC_CACHE_DIR"
  OPENCC_DOWNLOAD_OK=1
  for OPENCC_FILE in TSCharacters.txt TSPhrases.txt TWVariants.txt TWVariantsRevPhrases.txt; do
    OPENCC_TARGET="$OPENCC_CACHE_DIR/$OPENCC_FILE"
    # ver.1.3.1 is immutable, so a validated cached copy never needs refreshing.
    if [[ ! -s "$OPENCC_TARGET" ]]; then
      if /usr/bin/curl -L --fail --silent --show-error --connect-timeout 8 --max-time 45 \
          "$OPENCC_BASE_URL/$OPENCC_FILE" -o "$OPENCC_TARGET.download"; then
        mv "$OPENCC_TARGET.download" "$OPENCC_TARGET"
      else
        rm -f "$OPENCC_TARGET.download"
        OPENCC_DOWNLOAD_OK=0
      fi
    fi
  done

  if [[ "$OPENCC_DOWNLOAD_OK" -eq 1 ]] && \
     "$PYTHON3" Tools/build_tw2s_opencc.py \
       "$OPENCC_TS_CHARS" "$OPENCC_TS_PHRASES" \
       "$OPENCC_TW_VARIANTS" "$OPENCC_TW_REV_PHRASES" \
       "$OPENCC_T2S_TMP" --require-full; then
    T2S_FOR_BUILD="$OPENCC_T2S_TMP"
    success "已套用 OpenCC 1.3.1 完整台灣正體→簡體 tw2s 規則"
  else
    rm -f "$OPENCC_T2S_TMP"
    # A non-empty but truncated/corrupt cache must not poison future installs.
    # (Correct OpenCC 1.3.1 TSPhrases.txt contains 281 rules and passes validation.)
    rm -f "$OPENCC_TS_CHARS" "$OPENCC_TS_PHRASES" "$OPENCC_TW_VARIANTS" "$OPENCC_TW_REV_PHRASES"
    warn "無法取得或驗證完整 OpenCC 1.3.1 tw2s，改用 ZIP 內建台灣核心修正版簡體詞庫。"
  fi
else
  warn "找不到 python3，簡體轉換改用 ZIP 內建台灣核心修正版詞庫。"
fi
cp "$T2S_FOR_BUILD" "$RES/t2s.bin"
cp -R Licenses "$RES/Licenses"
cp -R Resources/zh-Hant.lproj "$RES/"
cp -R Resources/zh_TW.lproj "$RES/"

step "4/7 建立 App 圖示"
info "產生 macOS AppIcon.icns…"
xattr -c "$ICON_SOURCE" 2>/dev/null || true
rm -rf "$ICONSET" "$ICON_ICNS"
mkdir -p "$ICONSET"
for size in 16 32 128 256 512; do
  sips -z "$size" "$size" "$ICON_SOURCE" --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
  sips -z "$((size * 2))" "$((size * 2))" "$ICON_SOURCE" --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$ICON_ICNS"
xattr -cr "$ICON_ICNS"
cp "$ICON_ICNS" "$RES/AppIcon.icns"

success "App 圖示建立完成"

step "5/7 編譯逐音輸入法"
info "編譯 Core、InputMethodKit 與候選視窗模組…"
CFLAGS=(-std=c99 -Os -DNDEBUG -D_POSIX_C_SOURCE=200809L -mmacosx-version-min=12.0 -arch "$ARCH" -ffunction-sections -fdata-sections -I"$PWD/Core")
OBJCFLAGS=(-Os -DNDEBUG -fobjc-arc -mmacosx-version-min=12.0 -arch "$ARCH" -I"$PWD/Core" -I"$PWD/App")

for f in ZYDictionary ZYEngine ZYComposer ZYLearning ZYConversion; do
  xcrun clang "${CFLAGS[@]}" -c "Core/$f.c" -o "$OBJ/$f.o"
done
xcrun clang "${OBJCFLAGS[@]}" -c App/main.m -o "$OBJ/main.o"
xcrun clang++ "${OBJCFLAGS[@]}" -std=c++17 -c App/ZYRuntime.mm -o "$OBJ/ZYRuntime.o"
xcrun clang++ "${OBJCFLAGS[@]}" -std=c++17 -c App/ZYCandidatePanel.mm -o "$OBJ/ZYCandidatePanel.o"
xcrun clang++ "${OBJCFLAGS[@]}" -std=c++17 -c App/ZYAccessibilityCaret.mm -o "$OBJ/ZYAccessibilityCaret.o"
xcrun clang++ "${OBJCFLAGS[@]}" -std=c++17 -c App/ZYInputController.mm -o "$OBJ/ZYInputController.o"

xcrun clang++ -arch "$ARCH" -mmacosx-version-min=12.0 -Wl,-dead_strip \
  "$OBJ"/*.o -framework Cocoa -framework InputMethodKit -framework Carbon \
  -framework ApplicationServices -framework CoreFoundation \
  -o "$MACOS/ZhuYinInputMethod"
chmod 755 "$MACOS/ZhuYinInputMethod"
success "逐音輸入法二進位編譯完成"

step "6/7 簽署與驗證 App"
/usr/bin/plutil -lint "$CONTENTS/Info.plist"
# 下載或 Finder 同步帶入的延伸屬性會使 ad-hoc codesign 失敗。
xattr -cr "$APP"
/usr/bin/codesign --force --deep --sign - "$APP"
/usr/bin/codesign --verify --deep --strict "$APP"
success "App 簽署與驗證完成"

step "7/7 安裝與重新註冊輸入法"
notice "接下來可能要求輸入 macOS 管理員密碼。"
# 系統層是唯一正式安裝位置；先解除註冊並清理舊的系統層／使用者層副本。
DEST="/Library/Input Methods/逐音輸入法.app"
LEGACY_USER_DEST="$HOME/Library/Input Methods/逐音輸入法.app"
LEGACY_USER_V2="$HOME/Library/Input Methods/逐音輸入法2.app"
LEGACY_SYSTEM_V2="/Library/Input Methods/逐音輸入法2.app"
sudo -v

# 1. 先解除註冊建置目錄及舊版副本。
LSREGISTER="/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"
if [[ -f "$LSREGISTER" ]]; then
  "$LSREGISTER" -u "$APP" 2>/dev/null || true
  "$LSREGISTER" -u "$DEST" 2>/dev/null || true
  "$LSREGISTER" -u "$LEGACY_USER_DEST" 2>/dev/null || true
  "$LSREGISTER" -u "$LEGACY_USER_V2" 2>/dev/null || true
  "$LSREGISTER" -u "$LEGACY_SYSTEM_V2" 2>/dev/null || true
fi

sudo rm -rf "$DEST"
sudo rm -rf "$LEGACY_SYSTEM_V2"
rm -rf "$LEGACY_USER_DEST"
rm -rf "$LEGACY_USER_V2"
sudo mkdir -p "/Library/Input Methods"
# Desktop 的檔案提供者可能在等待管理員驗證期間重新加入 FinderInfo。
xattr -cr "$APP"
sudo cp -R "$APP" "$DEST"
/usr/bin/codesign --verify --deep --strict "$DEST"

# 1. 向 LaunchServices 註冊唯一的系統層安裝檔。
if [[ -f "$LSREGISTER" ]]; then
  "$LSREGISTER" -f "$DEST" 2>/dev/null || true
fi

# 2. 強制在背景啟動一次輸入法 App 服務以建立 IPC 連線與服務綁定
killall -9 ZhuYinInputMethod 逐音輸入法 逐音輸入法2 2>/dev/null || true
open "$DEST"
sleep 1

# 3. 重啟系統層級的 AppleSpell 與 InputMethodKit 快取
killall -9 AppleSpell InputMethodKit TextInputMenuAgent TextInputSwitcher 2>/dev/null || true

echo
success "逐音輸入法 已成功完成安裝與背景服務初始化！"
notice "快捷鍵：F9 切換繁／簡；\` 開啟 Emoji；' 開啟常用中文標點。"
info "請至 系統設定 → 鍵盤 → 文字輸入 → 編輯（點擊左下角 '+' 號，尋找『逐音輸入法』）。"
open "x-apple.systempreferences:com.apple.Keyboard-Settings.extension" 2>/dev/null || true
