"""brand_color / get_app_profile — a tool, not a resource, on purpose.

Three apps declare `theme: software (--app-accent: blue-500)` in AGENTS.md. None is
blue: toabackup runs auth/violet, toablog teal, toacontact green. Serving that
metadata as a static resource would freeze the lie. get_app_profile reads the app's
tokens.css and data-theme at call time instead — which is also why the apps checkout
is a read-only mount and not a submodule: a submodule pins a commit, and a pinned
commit is a frozen profile, i.e. the same failure in a new place.
"""

import re

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from toa_mcp.loader import RulesLoader
from toa_mcp.maps import BRANDS, TOKEN_SCALES
from toa_mcp.settings import Settings

RO = ToolAnnotations(readOnlyHint=True)

_DATA_THEME = re.compile(r"""data-theme["']?\s*[:=]\s*["']([a-z-]+)["']""")
_ACCENT_DECL = re.compile(r"--app-accent:\s*([^;]+);")
_VAR_REF = re.compile(r"var\(\s*(--[\w-]+)\s*\)")

# Capture the WHOLE selector, not just the [data-theme=...] part. The apps declare
# --app-accent twice per theme: a base block `[data-theme="auth"]` (dark, the
# default) and a light override `[data-mode="light"][data-theme="auth"]`. Matching
# only the data-theme fragment hits both, and the light one — being later in the
# file — silently wins. Dark is the reference (see theme-guidelines), so select the
# block whose selector carries no data-mode qualifier.
_BLOCK = re.compile(r"([^{}]*?)\{([^{}]*?)\}", re.S)
_MODE_QUALIFIED = re.compile(r"\[data-mode=")


def get_brand_payload(loader: RulesLoader, brand: str) -> dict:
    if brand not in BRANDS:
        raise ValueError(
            f"unknown brand {brand!r}. Valid brands: {', '.join(sorted(BRANDS))}"
        )
    return {"brand": brand, "data": loader.read_json(*BRANDS[brand])}


def get_token_scale_payload(loader: RulesLoader, name: str) -> dict:
    if name not in TOKEN_SCALES:
        raise ValueError(
            f"unknown token scale {name!r}. Valid: {', '.join(sorted(TOKEN_SCALES))}"
        )
    return {"name": name, "css": loader.read_text("design", "tokens", TOKEN_SCALES[name])}


def register(mcp: FastMCP, loader: RulesLoader, settings: Settings | None = None) -> None:
    settings = settings or Settings()  # type: ignore[call-arg]

    @mcp.tool(
        annotations=RO,
        title="Canonical brand colour",
        description="Resolve a role (primary|secondary|canvas|success|warning) or a "
        "category (portal|gaming|auth|infra|tools) against toa://design/brand.",
    )
    def brand_color(role: str) -> dict:
        b = loader.read_json("design", "brand.json")
        for section in ("brand", "status", "categories"):
            if role in b.get(section, {}):
                value = b[section][role]
                out: dict = {"role": role, "section": section, "value": value}
                ph = [p for p in b.get("placeholders", []) if p["field"].endswith(f".{role}")]
                if ph:
                    out["placeholder"] = ph[0]
                if value == "TBD":
                    out["unresolved"] = [u for u in b.get("unresolved", []) if role in u["field"]]
                return out
        if role == "canvas":
            return {"role": "canvas", "section": "root", "value": b["canvas"]}
        raise ValueError(f"unknown role {role!r}")

    @mcp.tool(
        annotations=RO,
        title="Get brand tokens",
        description="Fetch the canonical brand JSON for 'toaweb' or 'gamingforge'.",
    )
    def get_brand(brand: str) -> dict:
        return get_brand_payload(loader, brand)

    @mcp.tool(
        annotations=RO,
        title="Get token scale",
        description="Fetch a non-color token scale CSS file: 'radius', 'shadows', or 'spacing'.",
    )
    def get_token_scale(name: str) -> dict:
        return get_token_scale_payload(loader, name)

    @mcp.tool(
        annotations=RO,
        title="Live app profile",
        description=(
            "Resolve an app's ACTUAL accent by reading its tokens.css and data-theme at "
            "call time — not its AGENTS.md metadata, which is wrong for 3 of 3 apps "
            "checked. Requires the apps checkout mounted read-only via TOA_APPS_PATH."
        ),
    )
    def get_app_profile(app: str) -> dict:
        root = settings.apps_path
        if root is None:
            raise ValueError(
                "get_app_profile needs the apps checkout mounted read-only, but "
                "TOA_APPS_PATH is not set. Set it to the apps checkout and mount that "
                "path read-only into the container. Without it this tool cannot read "
                "live state."
            )
        if not root.is_dir():
            raise ValueError(
                f"TOA_APPS_PATH is set to {root} but that directory is not present. "
                "On AX41 this is the read-only mount; locally it is often absent — "
                "unset TOA_APPS_PATH to disable this tool."
            )

        app_dir = (root / app).resolve()
        if not app_dir.is_relative_to(root.resolve()) or not app_dir.is_dir():
            raise ValueError(f"unknown app {app!r} under {root}")

        tokens = app_dir / "frontend/app/assets/css/theme/tokens.css"
        if not tokens.is_file():
            return {
                "app": app,
                "resolved": False,
                "reason": f"no tokens.css at {tokens.relative_to(root)} — app may not "
                "use the toa Nuxt theme contract.",
            }
        css = tokens.read_text(encoding="utf-8")

        # Which data-theme does the app actually set?
        theme = None
        for candidate in ("frontend/app/app.vue", "frontend/nuxt.config.ts"):
            p = app_dir / candidate
            if p.is_file():
                m = _DATA_THEME.search(p.read_text(encoding="utf-8"))
                if m:
                    theme = m.group(1)
                    break

        # Effective --app-accent in the DARK reference mode. Walk every block, keep
        # only unqualified selectors (no [data-mode=...]), and prefer the one
        # matching the app's data-theme over :root.
        accent_expr, accent_from = None, None
        for selector, body in _BLOCK.findall(css):
            # Strip comments and keep only the last line — the raw capture drags in
            # any preceding comment banner, which would be reported as the selector.
            sel = re.sub(r"/\*.*?\*/", "", selector, flags=re.S).strip().splitlines()
            sel = sel[-1].strip() if sel else ""
            if _MODE_QUALIFIED.search(sel):
                continue                      # light override — not the reference
            m = _ACCENT_DECL.search(body)
            if not m:
                continue
            if theme and f'[data-theme="{theme}"]' in sel:
                accent_expr, accent_from = m.group(1).strip(), sel
                break                          # exact theme match wins
            if sel.startswith(":root") and accent_expr is None:
                accent_expr, accent_from = m.group(1).strip(), sel

        # Dereference one var(--x) hop against the primitive declarations.
        accent_hex = accent_expr
        if accent_expr and (vm := _VAR_REF.search(accent_expr)):
            pm = re.search(rf"{re.escape(vm.group(1))}:\s*([^;]+);", css)
            if pm:
                accent_hex = pm.group(1).strip()

        declared = None
        for agents_md in (app_dir / "AGENTS.md",):
            if agents_md.is_file():
                m = re.search(r"theme:\s*(.+)", agents_md.read_text(encoding="utf-8"))
                if m:
                    declared = m.group(1).strip()

        return {
            "app": app,
            "resolved": True,
            "mode": "dark (the reference mode; light overrides are ignored)",
            "data_theme": theme,
            "app_accent_expr": accent_expr,
            "app_accent": accent_hex,
            "accent_from_selector": accent_from,
            "declared_in_agents_md": declared,
            "metadata_matches_code": None if not declared else (
                theme is not None and theme in declared
            ),
            "source": "read live from tokens.css + data-theme, not from AGENTS.md",
        }
