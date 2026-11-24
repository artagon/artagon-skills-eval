"""Workspace-wide pytest configuration: Hypothesis profiles and --fail-on-skip plugin."""

from __future__ import annotations

import os
from typing import Final

import pytest
from hypothesis import settings

_SKIPPED_KEY: pytest.StashKey[list[str]] = pytest.StashKey[list[str]]()
_CI_TRUTHY: Final[frozenset[str]] = frozenset({"1", "true", "yes"})


def register_hypothesis_profiles() -> None:
    """Register standard workspace Hypothesis profiles (dev, ci, thorough)."""
    settings.register_profile("dev", max_examples=50, deadline=None)
    settings.register_profile("ci", max_examples=100, derandomize=True, deadline=None)
    settings.register_profile("thorough", max_examples=1000, deadline=None)


def resolve_hypothesis_profile() -> str:
    """Resolve active profile from HYPOTHESIS_PROFILE, falling back to ci when CI=1 else dev."""
    configured = os.environ.get("HYPOTHESIS_PROFILE", "").strip()
    if configured:
        return configured
    if os.environ.get("CI", "").strip().lower() in _CI_TRUTHY:
        return "ci"
    return "dev"


register_hypothesis_profiles()
settings.load_profile(resolve_hypothesis_profile())


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--fail-on-skip",
        action="store_true",
        default=False,
        help="Fail the pytest session if any test is skipped.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    config.stash[_SKIPPED_KEY] = []
    register_hypothesis_profiles()
    cli_profile = config.getoption("--hypothesis-profile", default=None)
    if not cli_profile:
        settings.load_profile(resolve_hypothesis_profile())


class _FailOnSkipPlugin:
    def __init__(self, config: pytest.Config) -> None:
        self._config = config

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.skipped and report.when in {"setup", "call"}:
            self._config.stash[_SKIPPED_KEY].append(report.nodeid)

    def pytest_sessionfinish(self, session: pytest.Session, exitstatus: int) -> None:
        skipped = self._config.stash[_SKIPPED_KEY]
        if self._config.getoption("--fail-on-skip") and skipped and exitstatus == 0:
            session.exitstatus = pytest.ExitCode.TESTS_FAILED


def pytest_sessionstart(session: pytest.Session) -> None:
    _ = session.config.pluginmanager.register(
        _FailOnSkipPlugin(session.config), name="fail_on_skip"
    )
