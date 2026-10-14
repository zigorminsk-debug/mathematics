#!/usr/bin/env python3
"""tools/sync_assets.py — copy the shared web interface and the content banks
into both applications.

    webapp/*            → windows/web/                         (embedded with go:embed)
    webapp/*            → android/app/src/main/assets/webapp/  (WebViewAssetLoader)
    dist/content/*.json → <both>/content/                      (bank, rules, ui, ...)

Run it locally after editing ``webapp/`` or the content sources::

    python3 tools/build_content.py && python3 tools/sync_assets.py

CI runs ``python3 tools/sync_assets.py --check`` and fails when a copy is stale,
so the committed asset folders can never drift away from the shared sources.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEBAPP = ROOT / "webapp"
CONTENT = ROOT / "dist" / "content"

TARGETS = [
    ("windows", ROOT / "windows" / "web"),
    ("android", ROOT / "android" / "app" / "src" / "main" / "assets" / "webapp"),
]

#: the shared answer-checker vectors are asserted by the Android unit tests too
EXTRA_FILES = [
    (CONTENT / "answer_vectors.json",
     ROOT / "android" / "app" / "src" / "test" / "resources" / "answer_vectors.json"),
]

SKIP_NAMES = {".DS_Store", "Thumbs.db"}


def copy_tree_into(src: Path, dst: Path, keep: set[str] = frozenset()) -> int:
    """Exact mirror: stale files (e.g. a removed bank) are deleted from the copy."""
    dst.mkdir(parents=True, exist_ok=True)
    wanted = {item.name for item in src.iterdir() if item.name not in SKIP_NAMES} | set(keep)
    for stale in sorted(dst.iterdir()):
        if stale.name not in wanted:
            shutil.rmtree(stale) if stale.is_dir() else stale.unlink()
    count = 0
    for item in sorted(src.iterdir()):
        if item.name in SKIP_NAMES:
            continue
        target = dst / item.name
        if item.is_dir():
            count += copy_tree_into(item, target)
        else:
            shutil.copy2(item, target)
            count += 1
    return count


def compare_manifest(src: Path, dst: Path) -> bool:
    """version.json сравниваем по смыслу: отметка ``built`` зависит от времени сборки.

    Всё остальное (версия, периоды, SHA-256 остальных файлов) должно совпадать
    байт в байт — иначе копия действительно устарела.
    """
    if not dst.exists():
        return False
    try:
        left = json.loads(src.read_text(encoding="utf-8"))
        right = json.loads(dst.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    left.pop("built", None)
    right.pop("built", None)
    return left == right


def compare_tree(src: Path, dst: Path, keep: set[str] = frozenset()) -> list[str]:
    """Return a list of human-readable differences (empty = identical)."""
    problems: list[str] = []
    if not dst.exists():
        return [f"missing directory {dst.relative_to(ROOT)}"]
    wanted = {item.name for item in src.iterdir() if item.name not in SKIP_NAMES} | set(keep)
    problems += [f"stale {item.relative_to(ROOT)}" for item in sorted(dst.iterdir()) if item.name not in wanted]
    for item in sorted(src.iterdir()):
        if item.name in SKIP_NAMES:
            continue
        target = dst / item.name
        if item.is_dir():
            problems.extend(compare_tree(item, target))
        elif not target.exists():
            problems.append(f"missing {target.relative_to(ROOT)}")
        elif item.name == "version.json" and compare_manifest(item, target):
            continue
        elif not filecmp.cmp(item, target, shallow=False):
            problems.append(f"outdated {target.relative_to(ROOT)}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify that the copies are up to date instead of writing them")
    args = ap.parse_args()

    if not WEBAPP.exists():
        print("webapp/ is missing — nothing to sync", file=sys.stderr)
        return 1
    if not CONTENT.exists():
        print("dist/content is missing — run tools/build_content.py first", file=sys.stderr)
        return 1

    print("Asset sync")
    problems: list[str] = []
    for src, dst in EXTRA_FILES:
        if args.check:
            if not dst.exists() or not filecmp.cmp(src, dst, shallow=False):
                problems.append(f"outdated {dst.relative_to(ROOT)}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  · {dst.relative_to(ROOT)}")
    for label, web_target in TARGETS:
        content_target = web_target / "content"
        if args.check:
            problems += compare_tree(WEBAPP, web_target, keep={"content"})
            problems += compare_tree(CONTENT, content_target)
            print(f"  · checking {label}: {web_target.relative_to(ROOT)}")
        else:
            files = copy_tree_into(WEBAPP, web_target, keep={"content"})
            files += copy_tree_into(CONTENT, content_target)
            print(f"  · {label}: {files} files → {web_target.relative_to(ROOT)}/")

    if args.check:
        if problems:
            print("  ✗ the asset copies are stale:", file=sys.stderr)
            for p in problems:
                print(f"      {p}", file=sys.stderr)
            print("    run: python3 tools/build_content.py && python3 tools/sync_assets.py",
                  file=sys.stderr)
            return 1
        print("  ✓ the asset copies are up to date")
    else:
        print("  ✓ done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
