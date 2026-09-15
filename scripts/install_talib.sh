#!/bin/sh
# TA-Lib fallback installer for Alpine/aarch64 and other platforms.
# Usage: sh scripts/install_talib.sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

if python -c 'import talib' >/dev/null 2>&1; then
  echo "TA-Lib already available: $(python -c 'import talib; print(talib.__version__)')"
  exit 0
fi

UV="${UV:-uv}"
if command -v "$UV" >/dev/null 2>&1; then
  echo "[1/3] Trying UV binary wheel..."
  if "$UV" add "TA-Lib>=0.8.0"; then
    "$UV" run python -c 'import talib; print("TA-Lib OK:", talib.__version__)'
    exit 0
  fi
fi

echo "[2/3] Trying pip binary wheel..."
if python -m pip install --upgrade --no-cache-dir TA-Lib; then
  python -c 'import talib; print("TA-Lib OK:", talib.__version__)'
  exit 0
fi

echo "[3/3] Binary wheel unavailable; installing build prerequisites..."
if command -v apk >/dev/null 2>&1; then
  apk add --no-cache build-base python3-dev musl-dev wget tar
fi

# The modern TA-Lib Python package can build its bundled C library.
python -m pip install --upgrade --no-cache-dir --no-binary TA-Lib TA-Lib
python -c 'import talib; print("TA-Lib source build OK:", talib.__version__)'
