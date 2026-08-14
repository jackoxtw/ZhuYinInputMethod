from pathlib import Path

root = Path(__file__).resolve().parents[1]
command = (root / 'Platforms/macOS/scripts/建立Release.command').read_text(encoding='utf-8')
build = (root / 'Platforms/macOS/scripts/build_and_install.command').read_text(encoding='utf-8')

assert command.startswith('#!/bin/bash\n')
assert 'set -euo pipefail' in command
assert 'build_and_install.command' in command
assert '--release-only' in command
assert 'exec ' in command
assert 'RELEASE_ONLY=0' in build
assert '--release-only' in build
assert 'Release/逐音輸入法-v$RELEASE_VERSION' in build

print('compile command static regression: OK')
