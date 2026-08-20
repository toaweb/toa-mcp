"""Standards lookup — needs logic, so it is a tool."""

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from toa_mcp.loader import RulesLoader
from toa_mcp.maps import STANDARDS, first_heading, route_task

RO = ToolAnnotations(readOnlyHint=True)


def list_standards_payload(loader: RulesLoader) -> dict:
    items = [
        {"key": k, "title": first_heading(loader.read_text("standards", f))}
        for k, f in sorted(STANDARDS.items())
    ]
    return {"count": len(items), "standards": items}


def get_standard_payload(
    loader: RulesLoader, name: str, section: str | None = None
) -> dict:
    if name not in STANDARDS:
        raise ValueError(
            f"unknown standard {name!r}. Known: {', '.join(sorted(STANDARDS))}"
        )
    text = loader.read_text("standards", STANDARDS[name])
    if section is None:
        return {"standard": name, "content": text, "lines": len(text.splitlines())}
    for block in text.split("\n## "):
        if section.lower() in block.split("\n", 1)[0].lower():
            return {
                "standard": name,
                "section": block.split("\n", 1)[0].strip(),
                "content": "## " + block,
            }
    raise ValueError(f"section {section!r} not found in {name}")


def get_standards_for_task_payload(loader: RulesLoader, task: str) -> dict:
    routing = loader.read_text("standards", "_routing.md")
    cats = route_task(task, routing)
    return {
        "task": task,
        "matched": len(cats),
        "categories": cats,
        "hint": None if cats else "No category matched — call list_standards().",
        "fallback": "toa://standards/index" if not cats else None,
    }


def register(mcp: FastMCP, loader: RulesLoader) -> None:
    @mcp.tool(
        annotations=RO,
        title="List standards",
        description="List every standard key with its one-line title.",
    )
    def list_standards() -> dict:
        return list_standards_payload(loader)

    @mcp.tool(
        annotations=RO,
        title="Which standards apply to this task",
        description="Map a task description to the standards that govern it. "
        "Backed by standards/_routing.md (16 task categories).",
    )
    def get_standards_for_task(task: str) -> dict:
        return get_standards_for_task_payload(loader, task)

    @mcp.tool(
        annotations=RO,
        title="Read a standard, optionally one section",
        description="Fetch a standard by name. Pass `section` to extract a single "
        "heading instead of the whole 200-600 line document.",
    )
    def get_standard(name: str, section: str | None = None) -> dict:
        return get_standard_payload(loader, name, section)
