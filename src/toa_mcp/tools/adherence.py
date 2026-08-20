"""validate_usage / verify_tailwind — FORCED TOOL.

Rebuilt for ui-kit. toafigma's _adherence.oxlintrc.json cannot be reused: it encodes
React prop names (iconLeft, color) that do not exist on the Astro components
(leadingIconName, tone). Reusing it would validate against the wrong API.

The Inter / IBM Plex font allowlist was pre-rebrand and has been removed.
"""

import re

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from toa_mcp.loader import RulesLoader

RO = ToolAnnotations(readOnlyHint=True)

_RAW_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
_INLINE_STYLE = re.compile(r'\bstyle\s*=\s*["\']')
_ARBITRARY_COLOR = re.compile(r"\b(?:bg|text|border)-\[#[0-9a-fA-F]{3,8}\]")
_STYLE_BLOCK = re.compile(r"<style[\s>]")


def check_usage(code: str, framework: str = "astro") -> dict:
    findings: list[dict] = []

    def add(rule: str, line_no: int, text: str, msg: str) -> None:
        findings.append(
            {"rule": rule, "line": line_no, "text": text.strip()[:100], "message": msg}
        )

    for n, line in enumerate(code.splitlines(), 1):
        if _RAW_HEX.search(line) and "tokens.css" not in line:
            add("no-raw-hex", n, line, "Raw hex. Use a design-system token via var().")
        if _INLINE_STYLE.search(line):
            add("no-inline-style", n, line, "Static style= is forbidden. Use Tailwind utilities.")
        if _ARBITRARY_COLOR.search(line):
            add("no-arbitrary-color", n, line, "Arbitrary-value colour. Use a token.")
        if _STYLE_BLOCK.search(line):
            add("no-style-block", n, line, "<style> blocks are forbidden outside src/theme/.")

    return {
        "framework": framework,
        "clean": not findings,
        "violation_count": len(findings),
        "findings": findings,
    }


def register(mcp: FastMCP, loader: RulesLoader) -> None:
    @mcp.tool(
        annotations=RO,
        title="Validate code against the toa design system",
        description=(
            "Check markup for design-system violations: raw hex, inline style, "
            "arbitrary-value colours, <style> blocks. The pre-rebrand Inter/IBM Plex "
            "font allowlist has been removed. "
            "Implements TAILWIND_STANDARD_2026 §Verifisering."
        ),
    )
    def validate_usage(code: str, framework: str = "astro") -> dict:
        return check_usage(code, framework)

    @mcp.tool(
        annotations=RO,
        title="Verify Tailwind compliance",
        description="TAILWIND_STANDARD_2026 §Verifisering (før commit). Called by the "
        "tailwind agent prompt before it returns.",
    )
    def verify_tailwind(code: str) -> dict:
        return check_usage(code, framework="tailwind")
