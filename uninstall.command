#!/bin/bash
set -euo pipefail
sudo -v
sudo rm -rf "/Library/Input Methods/逐音輸入法.app"
sudo rm -rf "/Library/Input Methods/逐音輸入法2.app"
rm -rf "$HOME/Library/Input Methods/逐音輸入法.app"
rm -rf "$HOME/Library/Input Methods/逐音輸入法2.app"
echo "已移除逐音輸入法的系統層與舊使用者層副本。若輸入來源仍顯示，登出再登入即可。"
