#!/usr/bin/env bash
# Render docs/assets/social-preview.svg to PNG (1280 × 640) for Settings → Social preview.
# Needs a local Chrome/Chromium; animations are frozen in their final state.
set -euo pipefail
cd "$(dirname "$0")/.."
chrome=$(command -v google-chrome || command -v chromium || command -v chromium-browser)
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
cp docs/assets/social-preview.svg "$tmp/a.svg"
printf '<html><body style="margin:0"><img src="a.svg" width="1280" height="640"></body></html>' > "$tmp/i.html"
"$chrome" --headless=new --disable-gpu --no-sandbox --hide-scrollbars --force-prefers-reduced-motion \
  --window-size=1280,640 --screenshot="$PWD/docs/assets/social-preview.png" "file://$tmp/i.html" >/dev/null 2>&1
echo "wrote docs/assets/social-preview.png"
