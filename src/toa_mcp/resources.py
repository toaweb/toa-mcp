"""toa:// resources. Static lookups only — anything needing logic is a tool."""

from mcp.server.fastmcp import FastMCP

from toa_mcp.loader import RulesLoader

_STANDARD_FILES = {
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
    "traefik": "TRAEFIK_STANDARD_2026.md",
    "versioning": "VERSIONING_STANDARD_2026.md",
}

_TOKEN_FILES = ("colors", "fonts", "primitives", "radius", "shadows", "spacing", "typography")


def register(mcp: FastMCP, loader: RulesLoader) -> None:
    # ---- standards -------------------------------------------------------
    @mcp.resource(
        "toa://standards/{name}",
        title="toa standard",
        description=f"One of the {len(_STANDARD_FILES)} canonical standards. Names: "
        + ", ".join(sorted(_STANDARD_FILES)),
        mime_type="text/markdown",
    )
    def standard(name: str) -> str:
        try:
            filename = _STANDARD_FILES[name]
        except KeyError:
            raise ValueError(
                f"unknown standard {name!r}. Known: {', '.join(sorted(_STANDARD_FILES))}"
            ) from None
        return loader.read_text("standards", filename)

    @mcp.resource("toa://standards/index", title="Standards index", mime_type="application/json")
    def standards_index() -> dict:
        return {"standards": sorted(_STANDARD_FILES), "routing": "use get_standards_for_task()"}

    # ---- rules -----------------------------------------------------------
    @mcp.resource("toa://rules/git", title="Git rules", mime_type="text/markdown")
    def rules_git() -> str:
        return loader.read_text("rules", "git.md")

    @mcp.resource("toa://rules/design", title="Design rules", mime_type="text/markdown")
    def rules_design() -> str:
        # TODO(catch-up): strip the self-declared stale @theme block (design.md:152-227)
        # and rewrite the `claude mcp remove` line client-neutrally before serving.
        return loader.read_text("rules", "design.md")

    # ---- design canon ----------------------------------------------------
    @mcp.resource("toa://design/brand", title="Canonical brand", mime_type="application/json")
    def design_brand() -> dict:
        return loader.read_json("design", "brand.json")

    @mcp.resource("toa://design/radius", title="Canonical radius scale", mime_type="application/json")
    def design_radius() -> dict:
        return loader.read_json("design", "radius.json")

    @mcp.resource("toa://design/typography", title="Canonical typography", mime_type="application/json")
    def design_typography() -> dict:
        return loader.read_json("design", "typography.json")

    @mcp.resource("toa://design/tokens/{name}", title="Design token file", mime_type="text/css")
    def design_token(name: str) -> str:
        if name not in _TOKEN_FILES:
            raise ValueError(f"unknown token file {name!r}. Known: {', '.join(_TOKEN_FILES)}")
        return loader.read_text("design", "tokens", f"{name}.css")

    @mcp.resource("toa://design/guidelines/{name}", title="Design guideline", mime_type="text/markdown")
    def design_guideline(name: str) -> str:
        gaps = loader.read_json("design", "guidelines", "_gaps.json")

        if (gap := gaps["missing"].get(name)) is not None:
            # Fail loudly and explain. toa-rules is derived only from pushed state,
            # so an unpushed ui-kit doc is absent by design, not by accident.
            raise ValueError(
                f"{name} is not available: {gap['reason']} "
                f"toa-rules is derived only from pushed state, so this is a known gap, "
                f"not a missing file. Fix: {gap['fix']} "
                f"(CATCH-UP.md item {gap['catch_up']})"
            )

        text = loader.read_text("design", "guidelines", f"{name}.md")

        if (stale := gaps["stale"].get(name)) is not None:
            # Valid content, just behind the working copy. Say so in-band rather than
            # letting an agent assume it is current.
            text = (
                f"> **Note — this is the pushed version ({stale['served_lines']} lines). "
                f"An unpushed working copy in ui-kit has {stale['unpushed_lines']} lines.** "
                f"Content below is valid but behind. See CATCH-UP.md item {stale['catch_up']}.\n\n"
                + text
            )
        return text

    @mcp.resource("toa://design/guidelines/index", title="Guidelines index", mime_type="application/json")
    def guidelines_index() -> dict:
        gaps = loader.read_json("design", "guidelines", "_gaps.json")
        return {
            "available": sorted(loader.list_stems("design/guidelines")),
            "missing": {k: v["reason"] for k, v in gaps["missing"].items()},
            "stale": gaps["stale"],
        }

    @mcp.resource("toa://design/styles", title="2026 web design styles", mime_type="text/markdown")
    def design_styles() -> str:
        return loader.read_text("design", "styles.md")

    @mcp.resource("toa://design/styles/index", title="Design styles index", mime_type="application/json")
    def design_styles_index() -> dict:
        return loader.read_json("design", "styles-index.json")

    @mcp.resource("toa://design/components/index", title="Component index", mime_type="application/json")
    def components_index() -> dict:
        return loader.manifest().get("components", {})

    @mcp.resource("toa://design/icons/index", title="Icon name index", mime_type="application/json")
    def icons_index() -> dict:
        return loader.read_json("design", "icons", "index.json")

    # ---- environment -----------------------------------------------------
    @mcp.resource("toa://env/ax41", title="AX41 production facts", mime_type="text/markdown")
    def env_ax41() -> str:
        return loader.read_text("env", "ax41.md")

    # App profiles are exposed only through the get_app_profile tool, which reads
    # live state from a TOA_APPS_PATH mount (Q4: read running truth, not a frozen
    # file). There is no static toa://apps/{app}/profile resource — the apps/
    # directory in the data layer was never populated, so the template resolved
    # to nothing for every app.

    # ---- meta ------------------------------------------------------------
    @mcp.resource("toa://meta/catch-up", title="Known catch-up debt", mime_type="text/markdown")
    def meta_catchup() -> str:
        return loader.read_text("CATCH-UP.md")
