#!/usr/bin/env bash
# Assembles the GitHub Pages site from the repository root:
# the two pages, the language switch, the book excerpts, the bridge for the browser, the aimodel package
# and the book's stored results.
# Usage: bash simulator/build_site.sh [output folder, default _site]
set -euo pipefail
OUT="${1:-_site}"
rm -rf "$OUT"
mkdir -p "$OUT/py" "$OUT/data"
cp simulator/index.html simulator/model.html simulator/dashboard.py simulator/i18n.js "$OUT/"
mkdir -p "$OUT/excerpt"
cp simulator/excerpt/*.pdf "$OUT/excerpt/"
cp -r aimodel "$OUT/py/"
find "$OUT/py" -name "__pycache__" -type d -prune -exec rm -rf {} +
cp outputs/headline.json outputs/sobol.json "$OUT/data/"
