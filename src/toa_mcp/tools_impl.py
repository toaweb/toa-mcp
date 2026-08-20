"""Assemble FastMCP tools for toa-mcp."""
from __future__ import annotations

import re

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from toa_mcp import content as C
from toa_mcp.content import Content, first_heading
from toa_mcp.models import (
    AppList,
    Brand,
    BrandList,
    DesignStylesPointer,
    EnvDoc,
    Finding,
    InfraProfile,
    RoutedCategory,
    StandardDoc,
    StandardList,
    StandardSummary,
    TaskRouting,
    TokenScale,
    TokenScaleList,
    ValidationResult,
)

RO = ToolAnnotations(readOnlyHint=True)

_STOPWORDS = frozenset({
    "the", "and", "for", "with", "this", "that", "when", "before", "after",
    "use", "using", "check", "write", "make", "add", "new", "work", "any",
    "from", "into", "your", "our", "are", "was", "has", "have", "not", "but",
})

_INSTRUCTIONS = (
    "Canonical standards and per-app infrastructure wiring for the toa:// "
    "ecosystem. Source of truth is the toa-rules checkout (TOA_RULES_HOME). "
    "Method and named design styles live in toa-agents (design-styles skill), not here. "
    "Call design_styles_info for the catalogue pointer; use get_brand for identity."
)

_STYLE_NAMES = [
    "brutalist", "editorial", "swiss-international", "premium-minimalism",
    "warm-minimalism", "typography-driven", "data-driven-saas",
    "industrial-technical", "immersive-storytelling", "organic-human-centered",
    "retro-vintage", "y2k-digital-nostalgia", "retro-terminal",
    "modern-corporate-design",
]


def build(store: Content) -> FastMCP:
    mcp = FastMCP(name="toa-rules", instructions=_INSTRUCTIONS)

    @mcp.tool(annotations=RO, title="List standards",
              description="List every standard key with its one-line title.")
    def list_standards() -> StandardList:
        items = []
        for k, f in sorted(C.STANDARDS.items()):
            try:
                title = first_heading(store.read_text("standards", f))
            except FileNotFoundError:
                continue
            items.append(StandardSummary(key=k, title=title))
        return StandardList(count=len(items), standards=items)

    @mcp.tool(annotations=RO, title="Get a standard",
              description="Fetch one standard by key. Optional section extracts one ## heading.")
    def get_standard(key: str, section: str | None = None) -> StandardDoc:
        if key not in C.STANDARDS:
            raise ValueError(
                f"unknown standard {key!r}. Valid keys: {', '.join(sorted(C.STANDARDS))}"
            )
        text = store.read_text("standards", C.STANDARDS[key])
        title = first_heading(text)
        if section is None:
            return StandardDoc(key=key, title=title, content=text, lines=len(text.splitlines()))
        for block in text.split("\n## "):
            head = block.split("\n", 1)[0].strip()
            if section.lower() in head.lower():
                body = block if block.startswith("#") else "## " + block
                return StandardDoc(key=key, title=title, section=head, content=body,
                                   lines=len(body.splitlines()))
        raise ValueError(f"section {section!r} not found in standard {key!r}")

    @mcp.tool(annotations=RO, title="Standards for a task",
              description="Map a task description to governing standards (_routing.md).")
    def get_standards_for_task(task: str) -> TaskRouting:
        routing = store.read_text(*C.ROUTING)
        q = {w for w in re.findall(r"\w+", task.lower())
             if len(w) > 2 and w not in _STOPWORDS}
        cats: list[RoutedCategory] = []
        for block in re.split(r"\n#{2,4} ", routing):
            head = block.split("\n", 1)[0].strip()
            hwords = set(re.findall(r"\w+", head.lower()))
            if q & hwords:
                cats.append(RoutedCategory(category=head, guidance=block[:600]))
        return TaskRouting(
            task=task, matched=len(cats), categories=cats,
            hint=None if cats else "No category matched — call list_standards().",
        )

    @mcp.tool(annotations=RO, title="List apps",
              description="List every app with an infra profile.")
    def list_apps() -> AppList:
        keys = sorted(C.APPS)
        return AppList(count=len(keys), apps=keys)

    @mcp.tool(annotations=RO, title="Get infra profile",
              description="App infrastructure wiring from toa-rules infra/apps.")
    def get_infra_profile(app: str) -> InfraProfile:
        if app not in C.APPS:
            raise ValueError(f"unknown app {app!r}. Valid apps: {', '.join(sorted(C.APPS))}")
        return InfraProfile(app=app, content=store.read_text("infra", "apps", C.APPS[app]))

    @mcp.tool(annotations=RO, title="Get environment facts",
              description="Host/environment facts (e.g. ax41).")
    def get_env(host: str) -> EnvDoc:
        if host not in C.ENV:
            raise ValueError(f"unknown host {host!r}. Valid hosts: {', '.join(sorted(C.ENV))}")
        return EnvDoc(host=host, content=store.read_text("env", C.ENV[host]))

    @mcp.tool(annotations=RO, title="List brands",
              description="List every brand key served by get_brand.")
    def list_brands() -> BrandList:
        keys = sorted(C.BRANDS)
        return BrandList(count=len(keys), brands=keys)

    @mcp.tool(annotations=RO, title="Get brand tokens",
              description="Canonical brand JSON for toaweb or gamingforge.")
    def get_brand(brand: str) -> Brand:
        if brand not in C.BRANDS:
            raise ValueError(
                f"unknown brand {brand!r}. Valid brands: {', '.join(sorted(C.BRANDS))}"
            )
        subdir, fname = C.BRANDS[brand]
        # subdir may be nested ("gf/design") — split so path never escapes via a single segment
        parts = tuple(p for p in subdir.split("/") if p) + (fname,)
        return Brand(brand=brand, data=store.read_json(*parts))

    @mcp.tool(annotations=RO, title="List token scales",
              description="List non-colour token scales (radius, shadows, spacing).")
    def list_token_scales() -> TokenScaleList:
        keys = sorted(C.TOKEN_SCALES)
        return TokenScaleList(count=len(keys), scales=keys)

    @mcp.tool(annotations=RO, title="Get token scale",
              description="Non-color token CSS: radius, shadows, or spacing.")
    def get_token_scale(name: str) -> TokenScale:
        if name not in C.TOKEN_SCALES:
            raise ValueError(
                f"unknown token scale {name!r}. Valid: {', '.join(sorted(C.TOKEN_SCALES))}"
            )
        return TokenScale(name=name, css=store.read_text("design", "tokens", C.TOKEN_SCALES[name]))

    @mcp.tool(annotations=RO, title="Where named design styles live",
              description="Pointer to the 14 styles in toa-agents design-styles skill.")
    def design_styles_info() -> DesignStylesPointer:
        return DesignStylesPointer(
            count=14,
            home="toa-agents skill `design-styles` → skills/design-styles/references/",
            styles=_STYLE_NAMES,
            note=(
                "When the user names an aesthetic, read the skill definition in full, "
                "then apply brand via get_brand / get_token_scale. "
                "Product UI behind login → product-ux skill, not this catalogue. "
                "Ignore legacy design/styles* under toa-rules — toa-agents is canonical."
            ),
        )

    _RAW_HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    _INLINE_STYLE = re.compile(r'\bstyle\s*=\s*["\']')
    _ARBITRARY_COLOR = re.compile(r"\b(?:bg|text|border)-\[#[0-9a-fA-F]{3,8}\]")
    _STYLE_BLOCK = re.compile(r"<style[\s>]")

    @mcp.tool(annotations=RO, title="Validate markup against the design system",
              description="Flag raw hex, inline style=, arbitrary colours, <style> blocks.")
    def validate_usage(code: str, framework: str = "astro") -> ValidationResult:
        findings: list[Finding] = []
        for n, line in enumerate(code.splitlines(), 1):
            if _RAW_HEX.search(line) and "tokens.css" not in line:
                findings.append(Finding(rule="no-raw-hex", line=n, text=line.strip()[:100],
                                        message="Raw hex. Use a design-system token."))
            if _INLINE_STYLE.search(line):
                findings.append(Finding(rule="no-inline-style", line=n, text=line.strip()[:100],
                                        message="Static style= is forbidden. Use utilities."))
            if _ARBITRARY_COLOR.search(line):
                findings.append(Finding(rule="no-arbitrary-color", line=n, text=line.strip()[:100],
                                        message="Arbitrary-value colour. Use a token."))
            if _STYLE_BLOCK.search(line):
                findings.append(Finding(rule="no-style-block", line=n, text=line.strip()[:100],
                                        message="<style> blocks are forbidden outside src/theme/."))
        return ValidationResult(framework=framework, clean=not findings,
                                violation_count=len(findings), findings=findings)

    return mcp
