"""Sole import site of official agentskills.io `skills-ref` producing frozen SkillFrontmatter."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Annotated

import skills_ref.errors
import skills_ref.parser
import skills_ref.validator
from expression import NOTHING, Error, Ok, Some
from pydantic import Field, ValidationError
from rpds import HashTrieMap

from artagon_eval_core.domain.errors import EvalResult, SchemaUsageError
from artagon_eval_core.domain.fp import NullableOption
from artagon_eval_core.domain.primitives import (
    NonEmptyStr,
    RelativeRepoPath,
    SkillId,
    static_redacted_literal,
)
from artagon_eval_core.domain.types import (
    FrozenModel,
    PersistentMap,
    empty_persistent_map,
)
from artagon_eval_core.ports.effects import SecretScrubberPort
from artagon_eval_core.runtime.redact import SecretVault


class SkillFrontmatter(FrozenModel):
    """Frozen Tier-0 agentskills.io manifest produced exclusively by spec_adapter."""

    name: SkillId
    description: Annotated[str, Field(min_length=1, max_length=1024)]
    license: NullableOption[NonEmptyStr] = NOTHING
    compatibility: NullableOption[Annotated[str, Field(min_length=1, max_length=500)]] = NOTHING
    allowed_tools: tuple[NonEmptyStr, ...] = ()
    metadata: PersistentMap[str, str] = Field(default_factory=empty_persistent_map)
    body_markdown: str
    skill_dir: Path
    skill_rel_dir: NullableOption[RelativeRepoPath] = NOTHING


def _read_skill_markdown(skill_dir: Path) -> EvalResult[str]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return Error(
            SchemaUsageError(
                reason_code="skill_md_missing",
                message=static_redacted_literal("SKILL.md not found in target skill directory"),
            )
        )
    try:
        raw = skill_md.read_text(encoding="utf-8").lstrip("\ufeff")
    except (OSError, UnicodeDecodeError):
        return Error(
            SchemaUsageError(
                reason_code="skill_md_unreadable",
                message=static_redacted_literal("Failed to read SKILL.md as UTF-8"),
            )
        )
    return Ok(raw)


def _optional_str(meta: Mapping[str, object], key: str) -> str | None:
    val = meta.get(key)
    if isinstance(val, str):
        cleaned = val.strip()
        return cleaned if cleaned else None
    return None


def _extract_metadata_map(raw_meta: object) -> HashTrieMap[str, str]:
    if not isinstance(raw_meta, Mapping):
        return HashTrieMap()
    return HashTrieMap({str(k): str(v) for k, v in raw_meta.items()})


def _to_frozen_frontmatter(
    meta: Mapping[str, object],
    *,
    body_markdown: str,
    skill_dir: Path,
    skill_rel_dir: RelativeRepoPath | None,
) -> SkillFrontmatter:
    name_raw = _optional_str(meta, "name") or ""
    desc_raw = _optional_str(meta, "description") or ""
    license_val = _optional_str(meta, "license")
    compat_val = _optional_str(meta, "compatibility")
    tools_str = _optional_str(meta, "allowed-tools") or ""
    return SkillFrontmatter(
        name=name_raw,
        description=desc_raw,
        license=Some(license_val) if license_val is not None else NOTHING,
        compatibility=Some(compat_val) if compat_val is not None else NOTHING,
        allowed_tools=tuple(tools_str.split()),
        metadata=_extract_metadata_map(meta.get("metadata")),
        body_markdown=body_markdown,
        skill_dir=skill_dir,
        skill_rel_dir=Some(skill_rel_dir) if skill_rel_dir is not None else NOTHING,
    )


def load_and_validate_spec_tier0(
    skill_dir: Path,
    *,
    skill_rel_dir: RelativeRepoPath | None = None,
    scrubber: SecretScrubberPort | None = None,
) -> EvalResult[SkillFrontmatter]:
    """Tier-0 validation delegating canonical agentskills.io rules to official `skills-ref`."""
    active_scrubber = SecretVault() if scrubber is None else scrubber
    raw_res = _read_skill_markdown(skill_dir)
    match raw_res:
        case Error(err):
            return Error(err)
        case Ok(raw_text):
            pass

    try:
        meta_dict, body = skills_ref.parser.parse_frontmatter(raw_text)
    except skills_ref.errors.ParseError as exc:
        return Error(
            SchemaUsageError(
                reason_code="skill_frontmatter_invalid",
                message=active_scrubber.scrub(str(exc)),
            )
        )

    spec_errors = skills_ref.validator.validate_metadata(meta_dict, skill_dir=skill_dir)
    if spec_errors:
        return Error(
            SchemaUsageError(
                reason_code="agentskills_spec_invalid",
                message=active_scrubber.scrub("; ".join(spec_errors)),
            )
        )

    try:
        frontmatter = _to_frozen_frontmatter(
            meta_dict,
            body_markdown=body,
            skill_dir=skill_dir,
            skill_rel_dir=skill_rel_dir,
        )
    except ValidationError as exc:
        return Error(
            SchemaUsageError(
                reason_code="agentskills_spec_invalid",
                message=active_scrubber.scrub(str(exc)),
            )
        )
    return Ok(frontmatter)
