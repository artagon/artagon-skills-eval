from __future__ import annotations

from dataclasses import dataclass

@dataclass
class SkillProperties:
    name: str
    description: str
    license: str | None = None
    compatibility: str | None = None
    allowed_tools: str | None = None
    metadata: dict[str, str] = ...

    def to_dict(self) -> dict[str, object]: ...
