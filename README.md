# toa-mcp

Minimal **Model Context Protocol** server for the `toa://` ecosystem.

Reads the **toa-rules** checkout and exposes standards, per-app infrastructure
wiring, brand tokens, and markup checks. **Named design styles** (brutalist,
Y2K, …) live in [toa-agents](https://github.com/toaweb/toa-agents)
(`design-styles` skill) — not in this server.

Successor to the old fat HTTP server and to **[toa-mcp2](https://github.com/toaweb/toa-mcp2)**
(same minimal surface; package renamed to `toa-mcp`). See [MIGRATION.md](./MIGRATION.md).

## Scope

| Serves | Does not serve |
|--------|----------------|
| Standards + task routing | Style essays / art direction method |
| Infra profiles + host env facts | Product UX patterns (`product-ux` skill) |
| Brand JSON + radius/shadows/spacing tokens | Invented brand values |
| `validate_usage` | Components / icons / Figma (out of scope) |
| `design_styles_info` (pointer only) | |

**Invariants:** one content source (`TOA_RULES_HOME`), explicit maps in
`content.py`, `readOnlyHint` on every tool, structured Pydantic outputs.

## Setup

```bash
# requires a toa-rules checkout
export TOA_RULES_HOME=~/projects/toa-rules   # or TOA_RULES_PATH

cd toa-mcp
uv sync
uv run toa-mcp          # stdio — default for Claude Code / Codex / Grok Build
```

Claude / MCP client config example:

```json
{
  "mcpServers": {
    "toa-rules": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/toa-mcp", "toa-mcp"],
      "env": { "TOA_RULES_HOME": "/path/to/toa-rules" }
    }
  }
}
```

## Tools

| Tool | Purpose |
|------|---------|
| `list_standards` | Keys + one-line titles |
| `get_standard` | Full doc or one `##` section |
| `get_standards_for_task` | Route a task string via `_routing.md` |
| `list_apps` / `get_infra_profile` | App wiring |
| `get_env` | Host facts (e.g. `ax41`) |
| `get_brand` | `toaweb` or `gamingforge` brand JSON |
| `get_token_scale` | `radius` \| `shadows` \| `spacing` CSS |
| `validate_usage` | Raw hex / inline style / arbitrary colors |
| `design_styles_info` | Pointer to toa-agents 14 styles |

## Layout

```
src/toa_mcp/
  content.py      # explicit maps + Content loader
  models.py       # Pydantic return types
  server.py       # stdio entry
  tools_impl.py   # FastMCP tool registration
evals/eval.xml
MIGRATION.md
```

## Adding content

Edit the maps in `content.py` and add the file under toa-rules. No directory
scanning — a missing map entry is intentional.

## License

Same as the toaweb account defaults for this repo.
