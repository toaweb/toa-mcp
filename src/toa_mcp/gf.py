"""gf:// — the GamingForge design system namespace.

Deliberately separate from toa://. Its brand rule is explicit: "do not copy
TOAWEB tokens or components." Data lives under gf/ in the toa-rules repo,
mirroring the toa design/ layout.

Components are plain Astro with no node:fs (unlike the toa ui-kit's Icon.astro),
so get_gf_component delivers them raw — no transform tool needed.
"""

from mcp.server.fastmcp import FastMCP

from toa_mcp.loader import RulesLoader


def _gf_manifest(loader: RulesLoader) -> dict:
    return loader.read_json("gf", "manifest.json")


def register(mcp: FastMCP, loader: RulesLoader) -> None:
    # ---- design canon ----------------------------------------------------
    @mcp.resource("gf://design/brand", title="GamingForge brand", mime_type="application/json")
    def gf_brand() -> dict:
        return loader.read_json("gf", "design", "brand.json")

    @mcp.resource("gf://design/radius", title="GamingForge radius scale", mime_type="application/json")
    def gf_radius() -> dict:
        return loader.read_json("gf", "design", "radius.json")

    @mcp.resource("gf://design/typography", title="GamingForge typography", mime_type="application/json")
    def gf_typography() -> dict:
        return loader.read_json("gf", "design", "typography.json")

    @mcp.resource("gf://design/tokens/{name}", title="GamingForge token file", mime_type="text/css")
    def gf_token(name: str) -> str:
        if name != "tokens":
            raise ValueError(f"unknown gf token file {name!r}. Known: tokens")
        return loader.read_text("gf", "design", "tokens", "tokens.css")

    @mcp.resource("gf://design/guidelines/{name}", title="GamingForge guideline", mime_type="text/markdown")
    def gf_guideline(name: str) -> str:
        gaps = loader.read_json("gf", "design", "guidelines", "_gaps.json")
        if (gap := gaps.get("missing", {}).get(name)) is not None:
            raise ValueError(
                f"{name} is not available: {gap['reason']} gf:// is derived only from "
                f"pushed state, so this is a known gap, not a missing file. Fix: {gap['fix']}"
            )
        return loader.read_text("gf", "design", "guidelines", f"{name}.md")

    @mcp.resource("gf://design/guidelines/index", title="GamingForge guidelines index", mime_type="application/json")
    def gf_guidelines_index() -> dict:
        gaps = loader.read_json("gf", "design", "guidelines", "_gaps.json")
        return {
            "available": sorted(loader.list_stems("gf/design/guidelines")),
            "missing": {k: v["reason"] for k, v in gaps.get("missing", {}).items()},
        }

    @mcp.resource("gf://design/components/index", title="GamingForge component index", mime_type="application/json")
    def gf_components_index() -> dict:
        return _gf_manifest(loader).get("components", {})

    # ---- component tool --------------------------------------------------
    @mcp.tool(
        title="Get a GamingForge component's source",
        description=(
            "Return one gamingforge-web-kit Astro component, raw. Unlike the toa "
            "ui-kit, these have no node:fs dependency, so no transform is needed. "
            "Check `status` (production|mock) before shipping."
        ),
    )
    def get_gf_component(name: str) -> dict:
        for c in _gf_manifest(loader).get("components", {}).get("items", []):
            if c["name"] == name:
                rel = c["source"].split(":", 1)[1]
                return {
                    "name": name,
                    "source": loader.read_text("gf", "design", "components", *rel.split("/")),
                    "status": c["status"],
                    "category": c["category"],
                    "deps": c["deps"],
                    "notes": c.get("notes"),
                }
        raise ValueError(f"unknown gf component {name!r} — see gf://design/components/index")

    @mcp.tool(
        title="List GamingForge components",
        description="Filter the gamingforge component index by status "
        "(production|mock) or category (ui, editorial, game, cards, ...).",
    )
    def list_gf_components(status: str | None = None, category: str | None = None) -> dict:
        items = _gf_manifest(loader).get("components", {}).get("items", [])
        if status:
            items = [c for c in items if c.get("status") == status]
        if category:
            items = [c for c in items if c.get("category") == category]
        return {"count": len(items), "components": [c["name"] for c in items]}
