"""Standards lookup — needs logic, so it is a tool."""

import re

from mcp.server.fastmcp import FastMCP

from toa_mcp.loader import RulesLoader


def register(mcp: FastMCP, loader: RulesLoader) -> None:
    @mcp.tool(
        title="Which standards apply to this task",
        description="Map a task description to the standards that govern it. "
        "Backed by standards/_routing.md (16 task categories).",
    )
    def get_standards_for_task(task: str) -> dict:
        routing = loader.read_text("standards", "_routing.md")
        q = set(re.findall(r"\w+", task.lower()))
        hits = []
        for block in routing.split("\n## "):
            head = block.split("\n", 1)[0].strip()
            if q & set(re.findall(r"\w+", head.lower())):
                hits.append({"category": head, "guidance": block[:600]})
        return {"task": task, "matched": len(hits), "sections": hits or None,
                "fallback": "toa://standards/index" if not hits else None}

    @mcp.tool(
        title="Read a standard, optionally one section",
        description="Fetch a standard by name. Pass `section` to extract a single "
        "heading instead of the whole 200-600 line document.",
    )
    def get_standard(name: str, section: str | None = None) -> dict:
        from toa_mcp.resources import _STANDARD_FILES

        if name not in _STANDARD_FILES:
            raise ValueError(f"unknown standard {name!r}. Known: {', '.join(sorted(_STANDARD_FILES))}")
        text = loader.read_text("standards", _STANDARD_FILES[name])
        if section is None:
            return {"standard": name, "content": text, "lines": len(text.splitlines())}
        for block in text.split("\n## "):
            if section.lower() in block.split("\n", 1)[0].lower():
                return {"standard": name, "section": block.split("\n", 1)[0].strip(),
                        "content": "## " + block}
        raise ValueError(f"section {section!r} not found in {name}")
