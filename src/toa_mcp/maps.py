"""Explicit content maps. Adding content = editing a map = a reviewable diff.

No globs, no directory scans. Shared by resources and tools so tests can
import the same tables the server uses.
"""

from __future__ import annotations

import re

# key -> filename under standards/
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
    "toaweb": "toaweb.md",
    "n8n": "n8n.md",
}

# host -> facts file under env/
ENV: dict[str, str] = {
    "ax41": "ax41.md",
}

# brand -> path parts for loader.read_json(*parts)
BRANDS: dict[str, tuple[str, ...]] = {
    "toaweb": ("design", "brand.json"),
    "gamingforge": ("gf", "design", "brand.json"),
}

# token scale -> css file under design/tokens/  (non-color scales only)
TOKEN_SCALES: dict[str, str] = {
    "radius": "radius.css",
    "shadows": "shadows.css",
    "spacing": "spacing.css",
}

# Trivial words that must not drive task→standard routing (avoid stopword
# matches like "and" hitting the "Priority And Safety" heading).
_STOPWORDS = frozenset({
    "the", "and", "for", "with", "this", "that", "when", "before", "after",
    "use", "using", "check", "write", "make", "add", "new", "work", "any",
    "from", "into", "your", "our", "are", "was", "has", "have", "not", "but",
})


def first_heading(text: str) -> str:
    """First markdown heading (or first non-empty line) — one-line summaries."""
    for line in text.splitlines():
        s = line.strip()
        if s:
            return s.lstrip("# ").strip()
    return ""


def route_task(task: str, routing_md: str) -> list[dict[str, str]]:
    """Match a task description against _routing.md headings (## through ####)."""
    q = {w for w in re.findall(r"\w+", task.lower()) if len(w) > 2 and w not in _STOPWORDS}
    cats: list[dict[str, str]] = []
    for block in re.split(r"\n#{2,4} ", routing_md):
        head = block.split("\n", 1)[0].strip()
        hwords = set(re.findall(r"\w+", head.lower()))
        if q & hwords:
            cats.append({"category": head, "guidance": block[:600]})
    return cats
