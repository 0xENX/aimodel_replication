#!/usr/bin/env bash
# Assembles the site of thereplacemind.com (Cloudflare Workers) from the repository root:
# the home page, the three tools, the language switch, the full book, the bridge for the browser, the aimodel package
# and the book's stored results.
# Usage: bash simulator/build_site.sh [output folder, default _site]
set -euo pipefail
OUT="${1:-_site}"
rm -rf "$OUT"
mkdir -p "$OUT/py" "$OUT/data"
cp simulator/index.html simulator/libro.html simulator/privacy.html simulator/sitemap.xml simulator/robots.txt simulator/home.css simulator/site.js simulator/topnav.css simulator/simulator.html simulator/model.html simulator/social.html simulator/dashboard.py simulator/i18n.js "$OUT/"
mkdir -p "$OUT/img" "$OUT/fonts"
cp simulator/libro.html "$OUT/book.html"   # the same book page, English address
cp simulator/fonts/* "$OUT/fonts/"
cp simulator/img/* "$OUT/img/"
# the book is sold on Amazon: the PDF and EPUB files are no longer published on the site
cp -r aimodel "$OUT/py/"
find "$OUT/py" -name "__pycache__" -type d -prune -exec rm -rf {} +
cp outputs/headline.json outputs/sobol.json "$OUT/data/"
