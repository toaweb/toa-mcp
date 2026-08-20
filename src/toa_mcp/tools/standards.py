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
    loader: RulesLoader,
    name: str | None = None,
    key: str | None = None,
    section: str | None = None,
) -> dict:
    ident = key or name
    if not ident:
        raise ValueError(
            f"pass name= or key=. Valid keys: {', '.join(sorted(STANDARDS))}"
        )
    if ident not in STANDARDS:
        raise ValueError(
            f"unknown standard {ident!r}. Valid keys: {', '.join(sorted(STANDARDS))}"
        )
    text = loader.read_text("standards", STANDARDS[ident])
    if section is None:
        return {"standard": ident, "content": text, "lines": len(text.splitlines())}
    for block in text.split("\n## "):
        head = block.split("\n", 1)[0].strip()
        if section.lower() in head.lower():
            body = block if block.startswith("#") else "## " + block
            return {"standard": ident, "section": head, "content": body}
    raise ValueError(f"section {section!r} not found in {ident}")


def get_standards_for_task_payload(loader: RulesLoader, task: str) -> dict:
    routing = loader.read_text("standards", "_routing.md")
    cats = route_task(task, routing)
    return {
        "task": task,
        "matched": len(cats),
        "categories": cats,
        "sections": cats or None,  # v1 alias
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
        "Backed by standards/_routing.md.",
    )
    def get_standards_for_task(task: str) -> dict:
        return get_standards_for_task_payload(loader, task)

    @mcp.tool(
        annotations=RO,
        title="Read a standard, optionally one section",
        description="Fetch a standard by name or key (same identifier list_standards "
        "returns). Pass `section` to extract a single heading instead of the whole "
        "200-600 line document.",
    )
    def get_standard(
        name: str | None = None,
        key: str | None = None,
        section: str | None = None,
    ) -> dict:
        return get_standard_payload(loader, name=name, key=key, section=section)
