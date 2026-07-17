"""get_component / list_components — FORCED TOOL.

ui/Icon.astro imports node:fs and node:path and reads SVGs off disk at build time.
15 components import it directly, ~55 transitively (32% of the library). An .astro
file served raw is therefore unusable to an agent. This tool resolves the import
closure (up to 21 files for SuperadminTemplate) and inlines the SVG bodies.
"""

import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from toa_mcp.loader import RulesLoader

_IMPORT = re.compile(r'^\s*import\s+(\w+)\s+from\s+["\'](\.[^"\']+\.astro)["\']', re.M)
_COMPONENTS = ("design", "components", "src", "components")


def register(mcp: FastMCP, loader: RulesLoader) -> None:
    def _entry(name: str) -> dict:
        for c in loader.manifest().get("components", {}).get("items", []):
            if c["name"] == name:
                return c
        raise ValueError(f"unknown component {name!r} — see toa://design/components/index")

    @mcp.tool(
        title="Get a component's source, resolved",
        description=(
            "Return one ui-kit Astro component with its import closure resolved and "
            "Icon.astro's node:fs SVG reads inlined. Always check `status` — 81 of 173 "
            "are propless mocks — and `brand_status`, which is `lagging` until ui-kit "
            "catches up to toa://design/brand."
        ),
    )
    def get_component(name: str) -> dict:
        entry = _entry(name)
        src_rel = entry["source"].split(":", 1)[1]
        source = loader.read_text("design", "components", *src_rel.split("/"))

        deps: dict[str, str] = {}
        pending, seen = [(src_rel, source)], {src_rel}
        while pending:
            rel, text = pending.pop()
            base = Path(rel).parent
            for _alias, imp in _IMPORT.findall(text):
                dep_rel = str((base / imp).resolve().relative_to(Path("/").resolve())) \
                    if imp.startswith("/") else str((base / imp))
                dep_rel = str(Path(dep_rel).as_posix())
                if dep_rel in seen:
                    continue
                seen.add(dep_rel)
                try:
                    dep_src = loader.read_text("design", "components", *dep_rel.split("/"))
                except FileNotFoundError:
                    continue
                deps[dep_rel] = dep_src
                pending.append((dep_rel, dep_src))

        return {
            "name": name,
            "source": source,
            "deps": deps,
            "status": entry["status"],
            "brand_status": entry["brand_status"],
            "kind": entry["kind"],
            "requires_transform": entry.get("requires_transform", False),
            "notes": entry.get("notes"),
            # TODO: inline Icon.astro's SVG bodies from the icon set before returning
            #       any component whose closure includes ui/Icon.astro.
        }

    @mcp.tool(
        title="List components",
        description="Filter the component index by status (production|mock|planned), "
        "brand_status (canonical|lagging) or kind.",
    )
    def list_components(
        status: str | None = None, brand_status: str | None = None, kind: str | None = None
    ) -> dict:
        items = loader.manifest().get("components", {}).get("items", [])
        for field, want in (("status", status), ("brand_status", brand_status), ("kind", kind)):
            if want:
                items = [c for c in items if c.get(field) == want]
        return {"count": len(items), "components": [c["name"] for c in items]}
