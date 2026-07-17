"""Reads toa-rules off disk. The only place that touches the data layer."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


class RulesLoader:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def _safe(self, *parts: str) -> Path:
        """Resolve under root and refuse anything that escapes it."""
        p = (self.root.joinpath(*parts)).resolve()
        if not p.is_relative_to(self.root):
            raise ValueError(f"path escapes toa-rules root: {'/'.join(parts)}")
        return p

    def read_text(self, *parts: str) -> str:
        p = self._safe(*parts)
        if not p.is_file():
            raise FileNotFoundError(f"not in toa-rules: {'/'.join(parts)}")
        return p.read_text(encoding="utf-8")

    def read_json(self, *parts: str) -> Any:
        return json.loads(self.read_text(*parts))

    def list_stems(self, subdir: str, suffix: str = ".md") -> list[str]:
        d = self._safe(subdir)
        return sorted(f.stem for f in d.glob(f"*{suffix}")) if d.is_dir() else []

    @lru_cache(maxsize=1)
    def manifest(self) -> dict[str, Any]:
        return self.read_json("manifest.json")

    def invalidate(self) -> None:
        self.manifest.cache_clear()
