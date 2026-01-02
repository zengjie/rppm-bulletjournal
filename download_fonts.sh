#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FONTS_DIR="$ROOT_DIR/fonts"

mkdir -p "$FONTS_DIR"

BASE_URL="https://raw.githubusercontent.com/octaviopardo/EBGaramond12/master/fonts/ttf"

curl -L --fail -o "$FONTS_DIR/EBGaramond-Regular.ttf" "$BASE_URL/EBGaramond-Regular.ttf"
curl -L --fail -o "$FONTS_DIR/EBGaramond-Italic.ttf" "$BASE_URL/EBGaramond-Italic.ttf"

echo "Downloaded fonts to $FONTS_DIR"
