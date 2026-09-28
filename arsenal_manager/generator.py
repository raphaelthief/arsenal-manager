from __future__ import annotations

import re
from pathlib import Path
from .constants import CATEGORY_CHOICES, PLATFORMS, TARGETS
from .models import Cheat


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "cheat"


def validate_title(title: str) -> list[str]:
    errors = []
    if not title.strip():
        errors.append("Title is required.")
    if "\n" in title or "\r" in title:
        errors.append("Title must be a single line.")
    return errors


def validate_cheat(cheat: Cheat) -> list[str]:
    errors = validate_title(cheat.title)
    if not cheat.command.strip():
        errors.append("Command is required.")
    if not cheat.categories:
        errors.append("At least one category is required.")
    unknown = sorted(set(cheat.categories) - set(CATEGORY_CHOICES))
    if unknown:
        errors.append("Unknown categories: " + ", ".join(unknown))
    if not cheat.platforms:
        errors.append("At least one platform is required.")
    if not cheat.targets:
        errors.append("At least one target is required.")
    return errors


def platform_tags(platforms: list[str]) -> list[str]:
    return [
        f"#plateform/{PLATFORMS.get(platform, platform).lower()}"
        for platform in platforms
    ]


def target_tags(targets: list[str]) -> list[str]:
    return [
        f"#target/{TARGETS.get(target, target).lower()}"
        for target in targets
    ]


def category_tags(categories: list[str]) -> list[str]:
    return [
        f"#cat/{category}"
        for category in categories
    ]


def render_markdown(cheat: Cheat) -> str:
    errors = validate_cheat(cheat)
    if errors:
        raise ValueError("\n".join(errors))

    lines = [
        "# CUSTOM",
        "",
    ]

    extra_tags = [
        tag.strip()
        for tag in cheat.tags
        if tag.strip()
    ]

    if extra_tags:
        lines.append(f"% {', '.join(extra_tags)}")
        lines.append("")

    tags = list(dict.fromkeys(
        platform_tags(cheat.platforms)
        + target_tags(cheat.targets)
        + category_tags(cheat.categories)
    ))

    if tags:
        lines.append(" ".join(tags))
        lines.append("")

    lines += [
        f"## {cheat.title.strip()}",
        "",
        cheat.description.strip(),
        "",
        "```",
        cheat.command.rstrip(),
        "```",
        "",
    ]

    return "\n".join(lines)


def write_cheat(cheat: Cheat, base_dir: Path) -> Path:
    filename = slugify(cheat.title) + ".md"
    path = base_dir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(cheat), encoding="utf-8")
    return path
