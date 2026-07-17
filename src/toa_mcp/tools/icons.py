"""find_icon — FORCED TOOL.

1173 icons across 19 categories cannot be 1173 resources. Production code imports
from @untitledui-pro/icons (npm), so the server only needs the name index (~30 KB),
not the 12 MB of SVG.

Note: CLAUDE.md claims 3066 icons across 18 categories. On disk: 1173 unique across
19. The per-category counts in CLAUDE.md are correct; the total is not.
"""

from mcp.server.fastmcp import FastMCP

from toa_mcp.loader import RulesLoader


def register(mcp: FastMCP, loader: RulesLoader) -> None:
    @mcp.tool(
        title="Find an Untitled UI icon",
        description=(
            "Search the Untitled UI PRO v1.6 line-icon name index by substring. "
            "Returns name + category. Import in code from @untitledui-pro/icons; "
            "never hand-write SVG paths, never add lucide/heroicons/phosphor."
        ),
    )
    def find_icon(query: str, category: str | None = None, limit: int = 20) -> dict:
        index = loader.read_json("design", "icons", "index.json")
        q = query.lower()
        hits = [
            i
            for i in index["icons"]
            if q in i["name"].lower() and (category is None or i["category"] == category)
        ]
        return {
            "query": query,
            "total_matches": len(hits),
            "categories": sorted(index["categories"]),
            "icons": hits[:limit],
        }
