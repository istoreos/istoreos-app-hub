#!/bin/sh
set -eu

generator="${1:-./bin/appcatalog}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

"$generator" --apps-root apps \
  --out-json "$tmp/catalog.json" --out-md "$tmp/catalog.min.md" \
  --out-md-full "$tmp/catalog.md" --out-diagnostics-jsonl "$tmp/diagnostics.jsonl"

cmp "$tmp/diagnostics.jsonl" docs/app-diagnostics.jsonl >/dev/null || {
  echo 'failed: docs/app-diagnostics.jsonl is stale; run make apps-catalog' >&2
  exit 1
}

command -v jq >/dev/null 2>&1 || { echo 'skip: jq required for semantic index checks'; exit 0; }
source_count="$(jq 'length' "$tmp/catalog.json")"
line_count="$(wc -l <"$tmp/diagnostics.jsonl" | tr -d ' ')"
unique_count="$(jq -sr 'map(.id) | unique | length' "$tmp/diagnostics.jsonl")"
[ "$source_count" = "$line_count" ] && [ "$line_count" = "$unique_count" ] || {
  echo "failed: source=$source_count lines=$line_count unique=$unique_count" >&2
  exit 1
}

jq -se 'map(.id) == (map(.id) | sort)' "$tmp/diagnostics.jsonl" >/dev/null
jq -e 'select(.id == "fastnet") | .autoconf == true and .luci == true and (.depends | index("fastnet") != null)' "$tmp/diagnostics.jsonl" >/dev/null
jq -e 'select(.type == "docker" and .istorec == true)' "$tmp/diagnostics.jsonl" >/dev/null

printf 'ok: compact app diagnostic index passed (%s apps, %s bytes)\n' "$line_count" "$(wc -c <"$tmp/diagnostics.jsonl" | tr -d ' ')"
