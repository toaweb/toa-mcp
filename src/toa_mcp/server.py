"""toa-mcp entry — FastMCP stdio server."""
from __future__ import annotations

from toa_mcp.content import Content, resolve_root
from toa_mcp.tools_impl import build


def main() -> None:
    build(Content(resolve_root())).run(transport="stdio")


if __name__ == "__main__":
    main()
