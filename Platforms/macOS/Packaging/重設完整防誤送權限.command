#!/bin/bash
set -euo pipefail
BUNDLE_ID='tw.zhuyin.inputmethod.v3'

echo '============================================================'
echo ' 逐音輸入法 — 重設「完整防誤送」輔助使用權限'
echo '============================================================'
echo

echo '[1/3] 清除舊的 Accessibility / Input Monitoring TCC 記錄…'
/usr/bin/tccutil reset Accessibility "$BUNDLE_ID" >/dev/null 2>&1 || true
/usr/bin/tccutil reset ListenEvent "$BUNDLE_ID" >/dev/null 2>&1 || true

echo '[2/3] 開啟「隱私權與安全性 → 輔助使用」…'
/usr/bin/open 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility' || true

echo '[3/3] 請將「逐音輸入法」重新允許後，切換到其他輸入法再切回逐音。'
echo '      接著到候選窗 → 設定，確認顯示「Guard：已就緒」；輸入中文時應變成「Guard：執行中」。'
echo
read -n 1 -s -r -p '按任意鍵關閉…'
echo
