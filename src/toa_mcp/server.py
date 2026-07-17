"""toa-rules MCP server — FastMCP over Streamable HTTP.

Verified against mcp 1.28.1:
  FastMCP.run(transport: Literal['stdio','sse','streamable-http'] = 'stdio', ...)
  FastMCP.streamable_http_app() -> Starlette

This module holds no rule content. Everything comes from toa-rules via RulesLoader.
"""

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from toa_mcp.auth import BearerTokenMiddleware
from toa_mcp.loader import RulesLoader
from toa_mcp.settings import Settings


def build_mcp(loader: RulesLoader, settings: Settings) -> FastMCP:
    mcp = FastMCP(
        name="toa-rules",
        instructions=(
            "Canonical rules, standards, design tokens and agent prompts for the toa:// "
            "ecosystem. The server is the source of truth; app code may lag behind it "
            "(see toa://meta/catch-up)."
        ),
        host=settings.mcp_host,
        port=settings.mcp_port,
        streamable_http_path="/mcp",
        log_level=settings.mcp_log_level,
    )

    from toa_mcp import prompts, resources
    from toa_mcp.tools import register_all as register_tools

    resources.register(mcp, loader)
    register_tools(mcp, loader, settings)
    prompts.register(mcp, loader)
    return mcp


def build_app(settings: Settings | None = None) -> Starlette:
    settings = settings or Settings()  # type: ignore[call-arg]
    loader = RulesLoader(settings.rules_path)
    mcp = build_mcp(loader, settings)

    inner: Starlette = mcp.streamable_http_app()
    inner.routes.append(
        Route("/healthz", lambda _r: JSONResponse({"status": "ok"}), methods=["GET"])
    )
    inner.add_middleware(BearerTokenMiddleware, token=settings.mcp_token)
    return inner


def main() -> None:
    settings = Settings()  # type: ignore[call-arg]
    uvicorn.run(
        build_app(settings),
        host=settings.mcp_host,
        port=settings.mcp_port,
        log_level=settings.mcp_log_level.lower(),
    )


if __name__ == "__main__":
    main()
