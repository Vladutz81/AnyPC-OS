#!/usr/bin/env bash
# Run every check. Must pass before each commit (see AGENTS.md).
set -euo pipefail
cd "$(dirname "$0")/.."

step() { printf '\n== %s\n' "$*"; }

step "Daemon unit tests"
(cd shell/daemon && python3 -m unittest discover -s tests)

step "Shell scripts syntax"
for f in session/anypc-session session/anypc-session-inner session/anypc-shelld session/anypc-update; do
  bash -n "$f"
done
if command -v shellcheck >/dev/null 2>&1; then
  shellcheck -S warning session/anypc-session session/anypc-session-inner session/anypc-shelld session/anypc-update
fi

step "Boot splash theme"
python3 scripts/check_splash.py

if command -v node >/dev/null 2>&1; then
  step "UI modules syntax"
  find shell/ui/js -name '*.js' -print0 | xargs -0 -n1 node --check
  step "UI strings present in every language"
  node scripts/check_i18n.mjs
else
  echo "node not found: skipping UI syntax and string checks"
fi

if python3 -c "import playwright" 2>/dev/null; then
  step "End-to-end UI test"
  python3 tests/e2e/test_shell.py
else
  echo "playwright not installed: skipping the end-to-end UI test"
fi

printf '\nAll checks passed.\n'
