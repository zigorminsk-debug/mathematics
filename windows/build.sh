#!/usr/bin/env bash
# Local/POSIX build helper (the released Windows binaries are produced by the
# GitHub Actions workflow .github/workflows/windows.yml).
#
#   ./windows/build.sh            # build for the host platform
#   GOOS=windows ./windows/build.sh
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
out="${OUT:-$root/dist/win}"
arch="${GOARCH:-$(go env GOARCH 2>/dev/null || echo amd64)}"

if command -v python3 >/dev/null 2>&1; then
  echo "==> syncing shared web assets and content bank"
  python3 "$root/tools/build_content.py"
  python3 "$root/tools/sync_assets.py"
fi

mkdir -p "$out"
cd "$here"
CGO_ENABLED=0 go build -trimpath -ldflags "-s -w -X main.buildStamp=$(date +%Y%m%d%H%M)" \
  -o "$out/CTPhysicsTutor-$arch" .
echo "==> built $out/CTPhysicsTutor-$arch"
