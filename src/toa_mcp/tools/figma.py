"""figma_export — FORCED TOOL.

The Figma export in design/figma-export/ is not valid CSS. Actual shape:

    'radius-sm': 6px;
    'spacing-xxs': 'var(--spacing-0&#8228;5-(2px))';
    'width-2xl': 'var(--spacing-256-(1,024px))';

Three defects make raw passthrough useless:
  1. Single-quoted keys, no `--` prefix, no :root{} wrapper.
  2. HTML entities in names (&#8228; is ONE DOT LEADER — Figma's "0.5").
  3. Parentheses and commas in identifiers — illegal in CSS.
"""

import html
import re

from mcp.server.fastmcp import FastMCP

from toa_mcp.loader import RulesLoader

_LINE = re.compile(r"^\s*'([^']+)'\s*:\s*(.+?);\s*$")

_EXPORT_FILES = {
    "primitives": "_primitives-style.css",
    "color-modes-dark": "1.-color-modes-dark-mode.css",
    "color-modes-light": "1.-color-modes-light-mode.css",
    "radius": "2.-radius-mode-1.css",
    "spacing": "3.-spacing-mode-1.css",
    "widths": "4.-widths-mode-1.css",
    "containers": "5.-containers-value.css",
    "typography": "6.-typography-value.css",
}


def _sanitize(name: str) -> str:
    """Figma name -> legal CSS custom-property identifier."""
    name = html.unescape(name)              # &#8228; -> '‥'
    name = re.sub(r"[^\w-]+", "-", name)    # parens, commas, dots -> '-'
    return re.sub(r"-{2,}", "-", name).strip("-")


def _rewrite_vars(value: str) -> str:
    """Rewrite every var(--name) reference, sanitizing the name inside.

    Figma names contain balanced parens — 'var(--spacing-256-(1,024px))'. A naive
    `var\\(--([^)]+)\\)` stops at the FIRST ')', leaving an unbalanced tail. Scan for
    the matching close paren instead.
    """
    out, i = [], 0
    while True:
        start = value.find("var(--", i)
        if start == -1:
            out.append(value[i:])
            return "".join(out)
        out.append(value[i:start])
        depth, j = 0, start + 3          # at the '(' of var(
        while j < len(value):
            if value[j] == "(":
                depth += 1
            elif value[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if j >= len(value):              # unterminated — emit verbatim
            out.append(value[start:])
            return "".join(out)
        inner = value[start + 6 : j]     # between 'var(--' and the matching ')'
        out.append(f"var(--{_sanitize(inner)})")
        i = j + 1


def register(mcp: FastMCP, loader: RulesLoader) -> None:
    @mcp.tool(
        title="Transform a raw Figma token export",
        description=(
            "Parse one Untitled UI PRO v8 Figma export file into usable CSS or JSON. "
            "The raw files are NOT valid CSS and cannot be served as resources. "
            f"Files: {', '.join(sorted(_EXPORT_FILES))}."
        ),
    )
    def figma_export(file: str, fmt: str = "css") -> dict:
        if file not in _EXPORT_FILES:
            raise ValueError(f"unknown export {file!r}. Known: {', '.join(sorted(_EXPORT_FILES))}")
        if fmt not in ("css", "json"):
            raise ValueError("fmt must be 'css' or 'json'")

        raw = loader.read_text("design", "figma-export", _EXPORT_FILES[file])
        tokens: dict[str, str] = {}
        skipped: list[str] = []
        for line in raw.splitlines():
            m = _LINE.match(line)
            if not m:
                if line.strip() and not line.lstrip().startswith(("/*", "*", "//")):
                    skipped.append(line.strip()[:60])
                continue
            key = _sanitize(m.group(1))
            value = _rewrite_vars(html.unescape(m.group(2)).strip().strip("'\""))
            tokens[key] = value

        if fmt == "json":
            return {"file": file, "tokens": tokens, "skipped_lines": skipped}
        body = "\n".join(f"  --{k}: {v};" for k, v in tokens.items())
        return {
            "file": file,
            "css": f":root {{\n{body}\n}}\n",
            "token_count": len(tokens),
            "skipped_lines": skipped,
        }
