from __future__ import annotations

import re
from pathlib import Path


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")

    if not text.lstrip().startswith("# "):
        errors.append("Missing level-1 title.")

    if "```" not in text:
        errors.append("Missing command code block.")

    if not re.search(r"#cat/", text):
        errors.append("Missing category tag.")

    if not re.search(r"#plateform/", text):
        errors.append("Missing platform tag.")

    if not re.search(r"#target/", text):
        errors.append("Missing target tag.")

    return errors


def validate_directory(directory: Path) -> tuple[int, list[tuple[Path, list[str]]]]:
    files = sorted(directory.rglob("*.md")) if directory.exists() else []
    problems = []
    for path in files:
        errors = validate_file(path)
        if errors:
            problems.append((path, errors))
    return len(files), problems
