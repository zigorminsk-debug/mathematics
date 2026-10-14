#!/usr/bin/env bash
# Local/POSIX build helper (the released Windows binaries are produced by the
# GitHub Actions workflow .github/workflows/windows.yml).
#
#   ./english/windows/build.sh            # build for the host platform
#   GOOS=windows ./english/windows/build.sh
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"          # english/
repo="$(cd "$here/../.." && pwd)"       # корень репозитория
out="${OUT:-$root/dist/win}"
arch="${GOARCH:-$(go env GOARCH 2>/dev/null || echo amd64)}"

if command -v python3 >/dev/null 2>&1; then
  echo "==> building the English content bank and syncing it into the app"
  CT_SUBJECT=english python3 "$root/tools/build_content.py"
  CT_SUBJECT=english python3 "$repo/tools/sync_assets.py"
fi

mkdir -p "$out"
cd "$here"
CGO_ENABLED=0 go build -trimpath -ldflags "-s -w -X main.buildStamp=$(date +%Y%m%d%H%M)" \
  -o "$out/CTEnglishTutor-$arch" .
echo "==> built $out/CTEnglishTutor-$arch"
