#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Amir Farhadi
"""Markdown Link Integrity Checker for winvda."""

import os
import re
import sys
import urllib.parse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

IGNORED_DIRS = {
    ".git",
    ".vs",
    ".vscode",
    "node_modules",
    ".ruff_cache",
    ".pytest_cache",
    ".venv",
    "venv",
}


def check_links() -> bool:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    md_files = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for file in files:
            if file.lower().endswith(".md"):
                md_files.append(Path(root) / file)

    link_pattern = re.compile(r"!?\[([^\]]*)\]\(([^)]+)\)")
    broken_links = []
    total_links = 0

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
            continue

        for match in link_pattern.finditer(content):
            text, target = match.groups()
            target = target.strip()

            if (
                target.startswith("http://")
                or target.startswith("https://")
                or target.startswith("mailto:")
                or target.startswith("#")
            ):
                continue

            target_path_str = target.split("#")[0].split("?")[0]
            if not target_path_str:
                continue

            target_path_str = urllib.parse.unquote(target_path_str)
            total_links += 1

            resolved_path = (md_file.parent / target_path_str).resolve()
            if not resolved_path.exists():
                broken_links.append(
                    {
                        "source_file": md_file.relative_to(REPO_ROOT).as_posix(),
                        "link_text": text,
                        "target": target,
                        "resolved": resolved_path,
                    }
                )

    print(f"Scanned {len(md_files)} markdown files, checked {total_links} local links.")
    if broken_links:
        print(f"\n[FAIL] Found {len(broken_links)} broken local links:")
        for b in broken_links:
            print(f"  In {b['source_file']}: '{b['link_text']}' -> '{b['target']}'")
        return False

    print("\n[SUCCESS] All local markdown links resolve successfully!")
    return True


if __name__ == "__main__":
    success = check_links()
    sys.exit(0 if success else 1)
