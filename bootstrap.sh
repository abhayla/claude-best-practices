#!/bin/bash
# Usage: curl -sL https://raw.githubusercontent.com/abhayla/claude-best-practices/main/bootstrap.sh | bash -s -- --stacks android-compose,fastapi-python
set -e

REPO="abhayla/claude-best-practices"
STACKS=""
TARGET="$(pwd)"

while [[ $# -gt 0 ]]; do
  case $1 in
    --stacks) STACKS="$2"; shift 2 ;;
    --target) TARGET="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [ -z "$STACKS" ]; then
  echo "Usage: bootstrap.sh --stacks android-compose,fastapi-python [--target /path]"
  echo ""
  echo "Available stacks: ai-gemini, android-compose, fastapi-python, firebase-auth, react-nextjs, superpowers"
  exit 1
fi

echo "Bootstrapping from $REPO with stacks: $STACKS"

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

git clone --depth=1 "https://github.com/$REPO.git" "$TMPDIR" 2>/dev/null
cd "$TMPDIR"
pip install -q pyyaml 2>/dev/null || pip3 install -q pyyaml 2>/dev/null

PYTHONPATH=. python scripts/bootstrap.py --stacks "$STACKS" --target "$TARGET" --hub "$TMPDIR"

echo ""
echo "Done! Next steps:"
echo "  cd $TARGET"
echo "  git add .claude/ CLAUDE.md && git commit -m 'feat: add Claude Code configuration from best practices hub'"
