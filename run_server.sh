#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

if ! command -v bundle >/dev/null 2>&1; then
  echo "Bundler is missing. Run this script in WSL Ubuntu with Ruby and Bundler installed." >&2
  exit 1
fi

echo "Checking Ruby dependencies..."
if ! bundle check; then
  bundle install
fi

echo "Starting Jekyll at http://localhost:4000 (startup on the Windows drive may take 1-3 minutes)..."
exec bundle exec ruby scripts/serve.rb --livereload --force_polling "$@"
