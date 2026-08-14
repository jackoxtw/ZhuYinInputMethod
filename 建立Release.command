#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
exec "$ROOT/Platforms/macOS/scripts/建立Release.command" "$@"
