"""Design-style lookup — the 2026 web design styles.

A tool (not just a resource) so an agent can (1) list styles to ask the user
which one, then (2) fetch just the chosen card instead of the whole document.
Cards live in design/styles.md; the catalogue in design/styles-index.json.
"""

from mcp.server.fastmcp import FastMCP

from toa_mcp.loader import RulesLoader


def register(mcp: FastMCP, loader: RulesLoader) -> None:
    @mcp.tool(
        title="List the 2026 web design styles",
        description="Return the catalogue of web design styles (key, id, name, "
        "essence, when-to-use) so you can offer the user a choice before designing a "
        "new site/page. Then call get_design_style for the chosen one. Full "
        "reference: toa://design/styles.",
    )
    def list_design_styles() -> dict:
        idx = loader.read_json("design", "styles-index.json")
        return {
            "styles": [
                {
                    "key": s["key"],
                    "id": s["id"],
                    "name": s["name"],
                    "essence": s["essence"],
                    "whenToUse": s["whenToUse"],
                }
                for s in idx["styles"]
            ],
            "crossCutting": idx.get("crossCutting"),
            "universalRules": idx.get("universalRules"),
        }

    @mcp.tool(
        title="Get one design style's implementation card",
        description="Return the full implementation card for a 2026 web design style "
        "(colour, type, layout, motion, texture, do/don't, when-to-use, tech "
        "enablers). Accepts the key ('A'), id ('dark-electric'), or a name keyword "
        "('brutalist'). Always apply the returned universalRules.",
    )
    def get_design_style(name: str) -> dict:
        idx = loader.read_json("design", "styles-index.json")
        q = name.strip().lower()
        match = None
        for s in idx["styles"]:
            if q == s["key"].lower() or q == s["id"].lower() or q in s["name"].lower():
                match = s
                break
        if match is None:
            known = ", ".join(f"{s['key']}={s['id']}" for s in idx["styles"])
            raise ValueError(f"unknown design style {name!r}. Known: {known}")

        text = loader.read_text("design", "styles.md")
        marker = f"### {match['key']}."
        card = None
        if marker in text:
            after = text.split(marker, 1)[1]
            for stop in ("\n### ", "\n## "):
                if stop in after:
                    after = after.split(stop, 1)[0]
                    break
            card = (marker + after).rstrip()

        # A style may ship a depth guide — the full working reference behind the
        # one-card summary. Load it inline so the agent has it in the same call,
        # rather than a pointer it has to chase (and may not reach headless).
        guide = None
        guide_path = match.get("guide")
        if guide_path:
            guide = loader.read_text("design", *guide_path.split("/"))

        return {
            "key": match["key"],
            "id": match["id"],
            "name": match["name"],
            "card": card,
            "guide": guide,
            "universalRules": idx.get("universalRules"),
            "note": "Apply universalRules to every style. The card is the summary; "
            "when a guide is present it is the full working reference — design to it. "
            "Cross-cutting techniques + full context: toa://design/styles.",
        }
