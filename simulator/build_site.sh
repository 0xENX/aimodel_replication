#!/usr/bin/env bash
# Assembles the GitHub Pages site from the repository root:
# the home page, the three tools, the language switch, the full book, the bridge for the browser, the aimodel package
# and the book's stored results.
# Usage: bash simulator/build_site.sh [output folder, default _site]
set -euo pipefail
OUT="${1:-_site}"
rm -rf "$OUT"
mkdir -p "$OUT/py" "$OUT/data"
cp simulator/index.html simulator/libro.html simulator/privacy.html simulator/home.css simulator/site.js simulator/topnav.css simulator/simulator.html simulator/model.html simulator/social.html simulator/dashboard.py simulator/i18n.js "$OUT/"
mkdir -p "$OUT/img" "$OUT/book" "$OUT/fonts"
cp simulator/fonts/* "$OUT/fonts/"
cp simulator/img/* "$OUT/img/"
cp simulator/book/*.pdf "$OUT/book/"
cp -r aimodel "$OUT/py/"
find "$OUT/py" -name "__pycache__" -type d -prune -exec rm -rf {} +
cp outputs/headline.json outputs/sobol.json "$OUT/data/"
