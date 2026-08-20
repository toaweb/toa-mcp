"""Infra profiles and environment facts — explicit maps, no globs."""

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from toa_mcp.loader import RulesLoader
from toa_mcp.maps import APPS, ENV

RO = ToolAnnotations(readOnlyHint=True)


def list_apps_payload() -> dict:
    keys = sorted(APPS)
    return {"count": len(keys), "apps": keys}


def get_infra_profile_payload(loader: RulesLoader, app: str) -> dict:
    if app not in APPS:
        raise ValueError(f"unknown app {app!r}. Valid apps: {', '.join(sorted(APPS))}")
    return {"app": app, "content": loader.read_text("infra", "apps", APPS[app])}


def get_env_payload(loader: RulesLoader, host: str) -> dict:
    if host not in ENV:
        raise ValueError(f"unknown host {host!r}. Valid hosts: {', '.join(sorted(ENV))}")
    return {"host": host, "content": loader.read_text("env", ENV[host])}


def register(mcp: FastMCP, loader: RulesLoader) -> None:
    @mcp.tool(
        annotations=RO,
        title="List apps",
        description="List every app with an infra profile.",
    )
    def list_apps() -> dict:
        return list_apps_payload()

    @mcp.tool(
        annotations=RO,
        title="Get infra profile",
        description="Fetch an app's infrastructure wiring (domain, Traefik, networks, "
        "ports, volumes, auth, backup) — provenance-backed, sourced from its compose.",
    )
    def get_infra_profile(app: str) -> dict:
        return get_infra_profile_payload(loader, app)

    @mcp.tool(
        annotations=RO,
        title="Get environment facts",
        description="Fetch host/environment facts (e.g. the AX41 production server).",
    )
    def get_env(host: str) -> dict:
        return get_env_payload(loader, host)
