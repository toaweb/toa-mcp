"""Explicit content maps + a path-guarded loader over the toa-rules checkout.

ONE serving mechanic: the explicit maps below. No globs, no directory scans
anywhere. Adding content = editing a map = a reviewable diff.

ONE content source: the toa-rules checkout, located via TOA_RULES_HOME. No
rule content is copied into this server repo.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# --- explicit maps -----------------------------------------------------------

# key -> filename under standards/  (22 canonical + tone, shipped day one)
STANDARDS: dict[str, str] = {
    "app-config": "APP_CONFIG_STANDARD_2026.md",
    "astro": "ASTRO_STANDARD_2026.md",
    "dependencies": "DEPENDENCIES_2026.md",
    "deployment-strategy": "DEPLOYMENT_STRATEGY_2026.md",
    "docker": "DOCKER_STANDARD_2026.md",
    "fastapi": "FASTAPI_STANDARD_2026.md",
    "favicon": "FAVICON_STANDARD_2026.md",
    "fonts": "FONTS_STANDARD_2026.md",
    "gallery": "GALLERY_STANDARD_2026.md",
    "git": "GIT_STANDARD_2026.md",
    "hugo": "HUGO_STANDARD_2026.md",
    "image": "IMAGE_STANDARD_2026.md",
    "mobile": "MOBILE_STANDARD_2026.md",
    "n8n": "N8N_STANDARD_2026.md",
    "nuxt-fastapi": "NUXT_FASTAPI_STANDARD_2026.md",
    "nuxt-vue": "NUXT_VUE_STANDARD_2026.md",
    "postgresql": "POSTGRESQL_STANDARD_2026.md",
    "seo": "SEO_STANDARD_2026.md",
    "stack-selection": "STACK_SELECTION_2026.md",
    "tailwind": "TAILWIND_STANDARD_2026.md",
    "tone": "TONE_STANDARD_2026.md",
    "traefik": "TRAEFIK_STANDARD_2026.md",
    "versioning": "VERSIONING_STANDARD_2026.md",
}

# app -> infra profile filename under infra/apps/
APPS: dict[str, str] = {
    "toabackup": "toabackup.md",
    "toablog": "toablog.md",
    "toacomments": "toacomments.md",
    "toacontact": "toacontact.md",
    "toadgs": "toadgs.md",
    "toafleet": "toafleet.md",
    "toaratings": "toaratings.md",
    "toaservers": "toaservers.md",
    "toaweb": "toaweb.md",   # static-hosting profile (Cloudflare Pages, no container)
    "n8n": "n8n.md",         # server-side decision record; full profile in BACKLOG.md
}

# host -> facts file under env/
ENV: dict[str, str] = {
    "ax41": "ax41.md",
}

# brand -> (subdir, json file)
BRANDS: dict[str, tuple[str, str]] = {
    "toaweb": ("design", "brand.json"),
    "gamingforge": ("gf/design", "brand.json"),
}

# token scale -> css file under design/tokens/  (audit-verified CURRENT set only)
TOKEN_SCALES: dict[str, str] = {
    "radius": "radius.css",
    "shadows": "shadows.css",
    "spacing": "spacing.css",
}

ROUTING = ("standards", "_routing.md")


# --- loader ------------------------------------------------------------------

class Content:
    """Reads toa-rules off disk, refusing any path that escapes the root."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _safe(self, *parts: str) -> Path:
        p = self.root.joinpath(*parts).resolve()
        if not p.is_relative_to(self.root):
            raise ValueError(f"path escapes TOA_RULES_HOME: {'/'.join(parts)}")
        return p

    def read_text(self, *parts: str) -> str:
        p = self._safe(*parts)
        if not p.is_file():
            raise FileNotFoundError(f"not in toa-rules: {'/'.join(parts)}")
        return p.read_text(encoding="utf-8")

    def read_json(self, *parts: str) -> Any:
        return json.loads(self.read_text(*parts))


def resolve_root() -> Path:
    """TOA_RULES_HOME (alias TOA_RULES_PATH; default ~/projects/toa-rules)."""
    raw = (
        os.environ.get("TOA_RULES_HOME")
        or os.environ.get("TOA_RULES_PATH")
        or str(Path.home() / "projects" / "toa-rules")
    )
    root = Path(raw).expanduser()
    if not root.is_dir():
        raise SystemExit(
            f"toa-mcp: TOA_RULES_HOME is not a readable directory: {root}\n"
            f"Set TOA_RULES_HOME to the toa-rules checkout "
            f"(default: ~/projects/toa-rules, a symlink to the checkout)."
        )
    if not (root / "standards").is_dir():
        raise SystemExit(
            f"toa-mcp: {root} does not look like a toa-rules checkout (no standards/).\n"
            f"Point TOA_RULES_HOME at the toa-rules content repo."
        )
    return root


def first_heading(text: str) -> str:
    """First markdown heading (or first non-empty line) — used for one-line summaries."""
    for line in text.splitlines():
        s = line.strip()
        if s:
            return s.lstrip("# ").strip()
    return ""
