#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
build_tmp="$(mktemp -d)"
combined_html="$build_tmp/mini-kochbuch.html"
chrome_profile="$build_tmp/chrome-profile"

cleanup() {
  rm -rf -- "$build_tmp"
}
trap cleanup EXIT

"$script_dir/generate.py"

manifest="$script_dir/rezepte/manifest.txt"
if [[ ! -s "$manifest" ]]; then
  echo "Kein Rezeptmanifest gefunden: $manifest" >&2
  exit 1
fi

recipe_files=()
while IFS= read -r recipe_name; do
  [[ -n "$recipe_name" ]] || continue
  recipe_file="$script_dir/rezepte/$recipe_name"
  if [[ ! -s "$recipe_file" ]]; then
    echo "Rezeptdatei aus Manifest fehlt: $recipe_file" >&2
    exit 1
  fi
  recipe_files+=("$recipe_file")
done < "$manifest"

{
  printf '%s\n' \
    '<!doctype html>' \
    '<html lang="de">' \
    '<head>' \
    '  <meta charset="utf-8">' \
    '  <meta name="viewport" content="width=device-width, initial-scale=1">' \
    '  <title>Mini-Kochbuch</title>' \
    '  <style>'
  sed 's#</style>#<\\/style>#g' "$script_dir/style.css"
  printf '%s\n' \
    '  </style>' \
    '</head>' \
    '<body>' \
    '<main>'

  for recipe_file in "${recipe_files[@]}"; do
    sed -n '1,$p' "$recipe_file"
  done

  printf '%s\n' \
    '</main>' \
    '</body>' \
    '</html>'
} > "$combined_html"

mkdir -p "$chrome_profile"

google-chrome \
  --headless \
  --disable-gpu \
  --no-sandbox \
  --user-data-dir="$chrome_profile" \
  --print-to-pdf="$script_dir/mini-kochbuch.pdf" \
  --print-to-pdf-no-header \
  "file://$combined_html"

echo "Erstellt: $script_dir/mini-kochbuch.pdf"
