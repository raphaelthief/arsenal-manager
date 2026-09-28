from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class Cheat:
    title: str
    description: str
    command: str
    categories: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)
    targets: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    path: Path | None = None
