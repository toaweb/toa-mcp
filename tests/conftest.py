"""Shared fixtures. Content comes from the sibling toa-rules checkout."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from toa_mcp.loader import RulesLoader


def _rules_root() -> Path:
    env = os.environ.get("TOA_RULES_PATH")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "toa-rules"


@pytest.fixture(scope="session")
def rules_path() -> Path:
    root = _rules_root()
    if not (root / "standards" / "TONE_STANDARD_2026.md").is_file():
        pytest.fail(f"toa-rules checkout not found at {root} (set TOA_RULES_PATH)")
    return root


@pytest.fixture(scope="session")
def loader(rules_path: Path) -> RulesLoader:
    return RulesLoader(rules_path)
