"""Prompts — 10 agent bodies + 5 task prompts.

The YAML frontmatter (name/description/tools/model) stays local in ~/.claude/agents/;
only the body is served, so Codex and Claude Code get the same instruction text.
"""

from mcp.server.fastmcp import FastMCP

from toa_mcp.loader import RulesLoader

_AGENTS = ("astro", "docker", "fastapi", "homelab", "hugo", "n8n", "nuxt-vue",
           "postgres", "security", "tailwind")

_TASKS = ("create-new-project", "generate-api-endpoint", "generate-component",
          "project-audit", "refactor-existing-project")


def register(mcp: FastMCP, loader: RulesLoader) -> None:
    def _make_agent(slug: str):
        def _fn() -> str:
            return loader.read_text("agents", f"{slug}.md")

        _fn.__name__ = f"agent_{slug.replace('-', '_')}"
        _fn.__doc__ = f"Domain instructions for {slug} work in the toa:// ecosystem."
        return _fn

    for slug in _AGENTS:
        mcp.prompt(name=f"toa:agent/{slug}", title=f"toa {slug} agent")(_make_agent(slug))

    def _make_task(slug: str):
        def _fn() -> str:
            return loader.read_text("prompts", "task", f"{slug}.md")

        _fn.__name__ = f"task_{slug.replace('-', '_')}"
        _fn.__doc__ = f"Reusable task prompt: {slug.replace('-', ' ')}."
        return _fn

    for slug in _TASKS:
        mcp.prompt(name=f"toa:task/{slug}", title=f"toa task: {slug}")(_make_task(slug))
