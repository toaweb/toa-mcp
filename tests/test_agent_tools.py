"""Ported v2 agent tools against the real toa-rules checkout."""

from __future__ import annotations

import pytest

from toa_mcp.loader import RulesLoader
from toa_mcp.maps import APPS, STANDARDS, first_heading, route_task
from toa_mcp.tools.adherence import check_usage
from toa_mcp.tools.brand import get_brand_payload, get_token_scale_payload
from toa_mcp.tools.infra import get_env_payload, get_infra_profile_payload, list_apps_payload
from toa_mcp.tools.standards import (
    get_standard_payload,
    get_standards_for_task_payload,
    list_standards_payload,
)


def test_list_standards_includes_tone(loader):
    payload = list_standards_payload(loader)
    keys = [s["key"] for s in payload["standards"]]
    assert "tone" in keys
    assert payload["count"] == len(STANDARDS)
    assert keys == sorted(keys)
    tone = next(s for s in payload["standards"] if s["key"] == "tone")
    assert tone["title"] == "Tekst & tone — Prosjektstandard 2026"


def test_get_standard_tone(loader):
    payload = get_standard_payload(loader, "tone")
    heading = first_heading(payload["content"])
    assert "tone" in heading.lower()
    assert heading == "Tekst & tone — Prosjektstandard 2026"


def test_get_standard_unknown(loader):
    with pytest.raises(ValueError, match=r"Valid keys:") as exc:
        get_standard_payload(loader, "nope")
    assert "tone" in str(exc.value)


def test_get_standard_accepts_key_alias(loader):
    by_name = get_standard_payload(loader, name="tone")
    by_key = get_standard_payload(loader, key="tone")
    assert by_name["content"] == by_key["content"]


def test_list_apps():
    payload = list_apps_payload()
    assert payload["count"] == 10
    assert payload["count"] == len(APPS)
    assert "n8n" in payload["apps"]
    assert "toaweb" in payload["apps"]
    assert payload["apps"] == sorted(APPS)


def test_get_infra_profile_toablog(loader):
    payload = get_infra_profile_payload(loader, "toablog")
    assert "DOMAIN_BLOG" in payload["content"]
    assert "/api/_auth" in payload["content"]


def test_get_infra_profile_toaweb(loader):
    payload = get_infra_profile_payload(loader, "toaweb")
    assert "Cloudflare Pages" in payload["content"]


def test_get_brand_toaweb(loader):
    payload = get_brand_payload(loader, "toaweb")
    assert payload["data"]["brand"]["primary"] == "#FF4E43"


def test_get_brand_gamingforge(loader):
    payload = get_brand_payload(loader, "gamingforge")
    assert payload["data"]["accent"]["primary"] == "#F05A28"


def test_get_env_ax41(loader):
    payload = get_env_payload(loader, "ax41")
    content = payload["content"]
    assert "AX41" in content or "65.108.43.225" in content


def test_get_token_scale_radius(loader):
    payload = get_token_scale_payload(loader, "radius")
    assert payload["name"] == "radius"
    assert payload["css"].strip()
    assert "radius" in payload["css"].lower() or "--" in payload["css"]


def test_get_token_scale_unknown(loader):
    with pytest.raises(ValueError, match=r"Valid:.*radius") as exc:
        get_token_scale_payload(loader, "colors")
    assert "shadows" in str(exc.value)
    assert "spacing" in str(exc.value)


def test_unknown_app_host_brand_list_valid(loader):
    with pytest.raises(ValueError, match=r"Valid apps:.*toaweb"):
        get_infra_profile_payload(loader, "nope")
    with pytest.raises(ValueError, match=r"Valid hosts:.*ax41"):
        get_env_payload(loader, "nope")
    with pytest.raises(ValueError, match=r"Valid brands:.*toaweb"):
        get_brand_payload(loader, "nope")


def test_get_standards_for_task_deploy(loader):
    payload = get_standards_for_task_payload(loader, "deploy docker traefik container")
    assert payload["matched"] >= 1
    categories = [c["category"] for c in payload["categories"]]
    assert any("Docker, Traefik, VPS, Deploy" in cat for cat in categories)
    assert payload["hint"] is None
    assert payload["sections"] == payload["categories"]


def test_route_task_ignores_stopwords(loader):
    routing = loader.read_text("standards", "_routing.md")
    cats = route_task("and for the", routing)
    assert not any("Priority And Safety" in c["category"] for c in cats)


async def test_mcp_registers_and_calls_new_tools(rules_path):
    from toa_mcp.server import build_mcp
    from toa_mcp.settings import Settings

    settings = Settings(rules_path=rules_path, mcp_token="t" * 32)
    mcp = build_mcp(RulesLoader(rules_path), settings)
    tools = {t.name for t in await mcp.list_tools()}
    expected = {
        "list_standards",
        "list_apps",
        "get_infra_profile",
        "get_env",
        "get_brand",
        "get_token_scale",
        "list_design_styles",
        "get_design_style",
        "get_standard",
        "get_standards_for_task",
        "validate_usage",
        "verify_tailwind",
        "brand_color",
        "get_app_profile",
    }
    assert expected <= tools
    result = await mcp.call_tool("list_standards", {})
    assert result is not None


def test_validate_usage_flags_hex_not_font():
    code = (
        "h1 { color: #FF4E43; }\n"
        "body { font-family: 'Space Grotesk'; }\n"
    )
    result = check_usage(code)
    rules = {f["rule"] for f in result["findings"]}
    assert "no-raw-hex" in rules
    assert "font-not-approved" not in rules
    font_only = check_usage("body { font-family: 'Space Grotesk'; }")
    assert font_only["clean"] is True
    assert font_only["violation_count"] == 0
