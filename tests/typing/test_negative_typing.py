"""Negative compile-time typing contract tests verifying basedpyright & mypy reject illegal states."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

NEGATIVE_SNIPPETS: dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]] = {
    "raw_str_in_redacted_error": (
        """
from artagon_eval_core.domain.errors import SchemaUsageError

err = SchemaUsageError(reason_code="bad", message="unredacted raw secret")
""",
        ("RedactedStr",),
        ("RedactedStr",),
    ),
    "mutate_frozen_model": (
        """
from artagon_eval_core.domain.errors import SchemaUsageError
from artagon_eval_core.domain.primitives import static_redacted_literal

err = SchemaUsageError(reason_code="bad", message=static_redacted_literal("ok"))
err.reason_code = "mutated"
""",
        ("read-only", "cannot be assigned", "frozen"),
        ("read-only", "frozen", "Cannot assign"),
    ),
    "mix_nominal_newtypes": (
        """
from artagon_eval_core.domain.primitives import CampaignId, parse_trial_id

def need_campaign(cid: CampaignId) -> str:
    return str(cid)

tid = parse_trial_id("trial-1")
_ = need_campaign(tid)
""",
        ("CampaignId",),
        ("CampaignId",),
    ),
    "ignore_eval_result_call": (
        """
from expression import Ok
from artagon_eval_core.domain.errors import EvalResult

def do_work() -> EvalResult[int]:
    return Ok(1)

do_work()
""",
        ("unused", "reportUnusedCallResult", "Result"),
        (),
    ),
    "explicit_any_banned_in_strict": (
        """
from typing import Any

payload: dict[str, Any] = {}
""",
        ("Any", "reportExplicitAny"),
        (),
    ),
}


def _run_checker(
    executable: str, target: Path, extra_args: tuple[str, ...] = ()
) -> subprocess.CompletedProcess[str]:
    bin_path = Path(sys.executable).parent / executable
    assert bin_path.is_file(), f"Missing {executable} at {bin_path}"
    return subprocess.run(
        [str(bin_path), *extra_args, str(target)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.typing
@pytest.mark.parametrize(
    ("case_name", "spec"),
    list(NEGATIVE_SNIPPETS.items()),
    ids=list(NEGATIVE_SNIPPETS.keys()),
)
def test_negative_typing_rejected_by_checkers(
    tmp_path: Path,
    case_name: str,
    spec: tuple[str, tuple[str, ...], tuple[str, ...]],
) -> None:
    snippet, pyright_markers, mypy_markers = spec
    sample = tmp_path / f"neg_{case_name}.py"
    _ = sample.write_text(snippet.lstrip(), encoding="utf-8")

    pyright_proc = _run_checker("basedpyright", sample)
    pyright_out = f"{pyright_proc.stdout}\n{pyright_proc.stderr}"
    assert pyright_proc.returncode != 0, (
        f"basedpyright unexpectedly accepted {case_name}:\n{pyright_out}"
    )
    assert any(m.lower() in pyright_out.lower() for m in pyright_markers), pyright_out

    if mypy_markers:
        mypy_proc = _run_checker("mypy", sample, ("--no-incremental",))
        mypy_out = f"{mypy_proc.stdout}\n{mypy_proc.stderr}"
        assert mypy_proc.returncode != 0, f"mypy unexpectedly accepted {case_name}:\n{mypy_out}"
        assert any(m.lower() in mypy_out.lower() for m in mypy_markers), mypy_out
