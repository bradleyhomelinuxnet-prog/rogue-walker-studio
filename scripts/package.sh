#!/usr/bin/env sh
# Build one installable .skill (zip) per skill folder into dist/.
set -e
cd "$(dirname "$0")/.."
mkdir -p dist
VER=$(cat VERSION)
for d in skills/*/; do
  n=$(basename "$d")
  rm -f "dist/$n.skill"
  (cd skills && zip -qr "../dist/$n.skill" "$n" -x '*/__pycache__/*' '*.pyc' '*/_txt/*')
  echo "dist/$n.skill"
done
(zip -qr "dist/rogue-walker-studio-$VER.zip" .claude-plugin skills examples README.md LICENSE CHANGELOG.md VERSION -x '*/__pycache__/*' '*.pyc')
echo "dist/rogue-walker-studio-$VER.zip"
