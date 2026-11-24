from __future__ import annotations

from pathlib import Path

from skills_ref.errors import ParseError, SkillError, ValidationError
from skills_ref.models import SkillProperties

def read_properties(skill_dir: Path) -> SkillProperties: ...
def find_skill_md(skill_dir: Path) -> Path | None: ...
def validate(skill_dir: Path) -> list[str]: ...
def to_prompt(skill_dirs: list[Path]) -> str: ...

__all__ = [
    "ParseError",
    "SkillError",
    "SkillProperties",
    "ValidationError",
    "find_skill_md",
    "read_properties",
    "to_prompt",
    "validate",
]
