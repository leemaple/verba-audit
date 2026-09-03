#!/usr/bin/env bash
# Disclosure and hygiene guard for the public verba-audit repository.
# Fails when tracked content contains pre-submission project state,
# manuscript drafts, exported discussions, credential patterns, or
# files large enough to be accidental data dumps.
set -euo pipefail

fail=0
note() { printf 'repo-guard: %s\n' "$1"; }
deny() { note "DENY $1"; fail=1; }

# Denylist of tracked path patterns (extended regex, case-insensitive).
deny_patterns=(
  '^\.paper-project/'
  '(^|/)discussion.*extract'
  '(^|/)review-packet'
  '(^|/)novelty'
  'claim[s]?\.md$'
  'manuscript'
  '\.docx$'
)

while IFS= read -r f; do
  for pat in "${deny_patterns[@]}"; do
    if [[ "$f" =~ $pat ]]; then
      deny "tracked path '$f' matches forbidden pattern '$pat'"
      break
    fi
  done
  # Credential-looking content inside tracked text files.
  if [[ -f "$f" && "$f" =~ \.(md|txt|sh|py|yml|yaml|json|toml)$ ]]; then
    if grep -nEi '(ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)' "$f" >/dev/null 2>&1; then
      deny "tracked file '$f' contains credential-like patterns"
    fi
  fi
  # Accidental data dumps.
  if [[ -f "$f" ]]; then
    size=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f" 2>/dev/null || printf 0)
    if (( size > 5242880 )); then
      deny "tracked file '$f' is larger than 5 MiB ($size bytes)"
    fi
  fi
done < <(git ls-files)

if (( fail )); then
  note 'blocked: remove the offending content and rewrite history if it was already pushed.'
  exit 1
fi
note 'ok: no forbidden paths, credentials, or oversized files tracked.'
