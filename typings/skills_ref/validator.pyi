from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

def validate_metadata(
    metadata: Mapping[str, object],
    skill_dir: Path | None = None,
) -> list[str]: ...
