#!/usr/bin/env bash
# Install the earshot CLI (MIT, https://github.com/Leonxlnx/earshot) into .venv-earshot
# and print the binary path. The PyPI name "earshot" is another project — always install from GitHub.
# Base install = make / sounds / sfx / kit (no models, no network at render time).
# Pass "listen" to also install the listening extra (~1.1 GB model download on first use).
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
VENV="${EARSHOT_VENV:-$ROOT/.venv-earshot}"
EXTRA=""
[ "${1:-}" = "listen" ] && EXTRA="[listen]"
if [ ! -x "$VENV/bin/earshot" ] || [ -n "$EXTRA" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q "earshot${EXTRA} @ git+https://github.com/Leonxlnx/earshot"
fi
"$VENV/bin/earshot" --version >/dev/null
echo "$VENV/bin/earshot"
