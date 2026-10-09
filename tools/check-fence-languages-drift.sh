#!/usr/bin/env bash
# The vendored fence-language table is a copy. Prove it still is.
#
# tools/fence-languages.json is carve-grammars' table, the one list every Carve
# editor grammar embeds fenced code from. A stale copy here would keep this
# syntax on an old list while the other editors moved on.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
local_file="$here/fence-languages.json"
upstream="${CARVE_GRAMMARS_DIR:-}"

if [[ -z "$upstream" ]]; then
  work="$(mktemp -d)"
  trap 'rm -rf "$work"' EXIT
  git clone --quiet --depth 1 https://github.com/markup-carve/carve-grammars "$work/cg"
  upstream="$work/cg"
fi

remote_file="$upstream/fence-languages/fence-languages.json"
if [[ ! -f "$remote_file" ]]; then
  echo "No fence-languages/fence-languages.json in $upstream" >&2
  exit 1
fi

if ! diff -q "$local_file" "$remote_file" >/dev/null; then
  echo "The vendored fence-language table has drifted from carve-grammars:"
  # `diff` exits 1 on a difference, which `pipefail` would turn into an abort
  # before the remediation line below.
  diff "$local_file" "$remote_file" | head -40 || true
  echo
  echo "Re-copy tools/fence-languages.json, then run tools/generate-fence-languages.py."
  exit 1
fi
printf 'check-fence-languages-drift: %s row(s) match carve-grammars.\n' \
  "$(python3 -c "import json,sys; print(len(json.load(open(sys.argv[1], encoding='utf-8'))['languages']))" "$local_file")"
