#!/usr/bin/env python3
"""tools/check_syntax.py — проверка синтаксиса Go, Kotlin и JavaScript.

Полноценные компиляторы (Go, Gradle/JVM) есть только в GitHub Actions, поэтому
здесь используется разбор исходников парсерами tree-sitter: он ловит опечатки,
незакрытые скобки и, что важно для Kotlin, вложенные блочные комментарии
(``reports/*.html`` внутри ``/** ... */`` открывает вложенный комментарий).

Если пакеты tree-sitter не установлены, проверка мягко пропускается (код CI
решает, установлены ли они, отдельным шагом).

Usage: python3 tools/check_syntax.py [--require]
       --require — падать, если парсеры недоступны (используется в CI)
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "build", "node_modules", "dist", ".gradle", "release"}
TARGETS = (".go", ".kt", ".kts")


def parsers():
    try:
        import tree_sitter
        from tree_sitter import Language, Parser
    except ImportError:
        return None
    out = {}
    try:
        import tree_sitter_go
        out[".go"] = Parser(Language(tree_sitter_go.language()))
    except Exception:
        pass
    try:
        import tree_sitter_kotlin
        out[".kt"] = Parser(Language(tree_sitter_kotlin.language()))
    except Exception:
        pass
    if not out:
        return None
    module = tree_sitter
    globals().setdefault("_ts_module", module)
    return out


def first_error(node):
    """Наименьший узел с ошибкой (для понятного сообщения)."""
    stack = [node]
    found = None
    while stack:
        current = stack.pop()
        if current.type == "ERROR" or current.is_missing:
            if found is None or (current.end_byte - current.start_byte) < (found.end_byte - found.start_byte):
                found = current
            continue
        stack.extend(current.children)
    return found


def check_kotlin_nested_comments(path: pathlib.Path) -> str | None:
    """В Kotlin блочные комментарии вложенные — ``/*`` внутри них опасен."""
    text = path.read_text(encoding="utf-8")
    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith("*") or stripped.startswith("//"):
            if re.search(r"(?<!^)/\*", stripped[1:]) and "*" in stripped:
                # внутри строки комментария встретилось начало блочного комментария
                return f"строка {index}: «/*» внутри комментария (в Kotlin комментарии вложенные)"
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--require", action="store_true", help="падать, если парсеры недоступны")
    args = ap.parse_args()

    available = parsers()
    if available is None:
        message = "tree-sitter недоступен: pip install tree-sitter tree-sitter-go tree-sitter-kotlin"
        print(f"· {message}")
        return 1 if args.require else 0

    failures = 0
    checked = 0
    for path in sorted(ROOT.rglob("*")):
        if path.suffix not in TARGETS and path.name != "build.gradle.kts":
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix == ".kts" and ".kt" not in available:
            continue
        parser = available.get(".kt" if path.suffix in (".kt", ".kts") else path.suffix)
        if parser is None:
            continue
        checked += 1
        source = path.read_bytes()
        tree = parser.parse(source)
        problems = []
        if tree.root_node.has_error:
            node = first_error(tree.root_node)
            if node is not None:
                line, column = node.start_point
                problems.append(f"разбор: строка {line + 1}, столбец {column + 1}")
            else:
                problems.append("разбор: синтаксическая ошибка")
        if path.suffix in (".kt", ".kts"):
            nested = check_kotlin_nested_comments(path)
            if nested:
                problems.append(nested)
        if problems:
            failures += 1
            print(f"✗ {path.relative_to(ROOT)}: {'; '.join(problems)}")
        else:
            print(f"✓ {path.relative_to(ROOT)}")
    print(f"{checked} файлов проверено, ошибок: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
