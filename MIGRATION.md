# Migration to toa-mcp 0.2

## From toa-mcp2

| Change | Detail |
|--------|--------|
| Clone | `https://github.com/toaweb/toa-mcp` |
| CLI | `toa-mcp` (not `toa-mcp2`) |
| Package | `toa_mcp` |
| Env | Prefer `TOA_RULES_HOME`; `TOA_RULES_PATH` still works |
| Tools | Same core set + `design_styles_info` (pointer to toa-agents) |

Client config example:

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

Then delete or archive **toa-mcp2**.

## From the old fat HTTP toa-mcp

Removed on purpose (not a regression):

- Streamable HTTP / Docker / Compose / Bearer auth
- Components, icons, Figma export, GF packs, style essays
- Resource-style `toa://…` surface beyond what tools cover

Use **stdio** + **toa-agents** (`design-styles`, `product-ux`) for method and aesthetics.
Brand and standards stay on this MCP via `get_brand`, `get_standard`, etc.

## Design styles

Named styles (brutalist, Y2K, …) are **not** served here. Call `design_styles_info`,
then read [toa-agents](https://github.com/toaweb/toa-agents) `skills/design-styles/`.
