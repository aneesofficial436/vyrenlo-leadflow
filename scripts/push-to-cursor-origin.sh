#!/usr/bin/env bash
# Run inside WSL from repo root: bash scripts/push-to-cursor-origin.sh
set -euo pipefail

REPO_NAME="${1:-vyrenlo-leadflow}"

if ! command -v origin &>/dev/null; then
  if [[ -x "$HOME/.local/bin/origin" ]]; then
    export PATH="$HOME/.local/bin:$PATH"
  else
    echo "Installing origin CLI..."
    curl -fsSL https://downloads.cursor.com/origin/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
  fi
fi

if ! origin auth status 2>/dev/null | grep -qi signed; then
  echo "Sign in to Cursor Origin (browser will open)..."
  origin auth login
fi

if git remote get-url origin &>/dev/null; then
  echo "Remote 'origin' already exists. Push with: git push -u origin main"
  exit 0
fi

echo "Creating Origin repo: $REPO_NAME"
CREATE_OUT="$(origin repo create "$REPO_NAME")"
echo "$CREATE_OUT"

URL="$(echo "$CREATE_OUT" | grep -Eo 'https://origin\.cursor\.com/[^ ]+' | head -1)"
if [[ -z "$URL" ]]; then
  echo "Could not parse clone URL. Add origin manually from the output above."
  exit 1
fi

git remote add origin "$URL"
git push -u origin main
echo "Done. Repository pushed to Cursor Origin."