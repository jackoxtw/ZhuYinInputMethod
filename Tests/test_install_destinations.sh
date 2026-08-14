#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INSTALLER="$ROOT/Platforms/macOS/scripts/build_and_install.command"
UNINSTALLER="$ROOT/Platforms/macOS/scripts/uninstall.command"
README="$ROOT/README.md"
PLIST="$ROOT/Platforms/macOS/App/Info.plist"
SYSTEM_APP='/Library/Input Methods/逐音輸入法.app'
USER_APP='$HOME/Library/Input Methods/逐音輸入法.app'

fail() { echo "FAIL: $*" >&2; exit 1; }

bash -n "$INSTALLER"
bash -n "$UNINSTALLER"

rg -Fq 'BUILD="/private/tmp/zhu-yin-input-method-native-$ARCH"' "$INSTALLER" || fail 'installer must build outside Desktop file-provider storage'
rg -Fq 'ICON_SOURCE="$PWD/icon/icon.png"' "$INSTALLER" || fail 'installer must use icon/icon.png as its icon source'
rg -Fq 'iconutil -c icns "$ICONSET" -o "$ICON_ICNS"' "$INSTALLER" || fail 'installer must create AppIcon.icns'
rg -Fq 'cp "$ICON_ICNS" "$RES/AppIcon.icns"' "$INSTALLER" || fail 'installer must bundle AppIcon.icns'
rg -Fq '<key>CFBundleIconFile</key><string>AppIcon.icns</string>' "$PLIST" || fail 'Info.plist must define AppIcon.icns as the app icon'
[[ $(rg -F '<string>AppIcon.icns</string>' "$PLIST" | wc -l | tr -d ' ') -eq 4 ]] || fail 'all input-method icon references must use AppIcon.icns'
XATTR_LINE=$(rg -n -F 'xattr -cr "$APP"' "$INSTALLER" | cut -d: -f1)
SIGN_LINE=$(rg -n -F '/usr/bin/codesign --force --deep --sign - "$APP"' "$INSTALLER" | cut -d: -f1)
SIGN_XATTR_LINE=$(printf '%s\n' "$XATTR_LINE" | awk -v sign="$SIGN_LINE" '$1 < sign {line=$1} END {print line}')
COPY_LINE=$(rg -n -F 'sudo cp -R "$APP" "$DEST"' "$INSTALLER" | cut -d: -f1)
COPY_XATTR_LINE=$(printf '%s\n' "$XATTR_LINE" | awk -v copy="$COPY_LINE" '$1 < copy {line=$1} END {print line}')
[[ -n "$SIGN_XATTR_LINE" && "$SIGN_XATTR_LINE" -lt "$SIGN_LINE" && "$SIGN_XATTR_LINE" -gt 40 ]] || fail 'installer must clear build-bundle extended attributes immediately before signing'
[[ -n "$COPY_XATTR_LINE" && "$COPY_XATTR_LINE" -gt "$SIGN_LINE" && "$COPY_XATTR_LINE" -lt "$COPY_LINE" ]] || fail 'installer must clear build-bundle extended attributes immediately before system copy'
rg -Fq "DEST=\"$SYSTEM_APP\"" "$INSTALLER" || fail 'installer must use the system-level destination'
rg -Fq "sudo cp -R \"\$APP\" \"\$DEST\"" "$INSTALLER" || fail 'installer must copy to the system-level destination with sudo'
rg -Fq "sudo rm -rf \"\$DEST\"" "$INSTALLER" || fail 'installer must replace the existing system-level bundle with sudo'
rg -Fq "LEGACY_USER_DEST=\"$USER_APP\"" "$INSTALLER" || fail 'installer must identify the legacy user-level bundle'
rg -Fq 'rm -rf "$LEGACY_USER_DEST"' "$INSTALLER" || fail 'installer must remove the legacy user-level bundle'
rg -Fq "sudo rm -rf \"$SYSTEM_APP\"" "$UNINSTALLER" || fail 'uninstaller must remove the system-level bundle with sudo'
rg -Fq "rm -rf \"$USER_APP\"" "$UNINSTALLER" || fail 'uninstaller must remove a legacy user-level bundle'
rg -Fq "\`$SYSTEM_APP\`" "$README" || fail 'README must document the system-level destination'

echo 'test_install_destinations: OK'
