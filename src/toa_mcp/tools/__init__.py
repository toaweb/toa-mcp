"""Tools — anything that needs logic, search or transformation.

The four forced cases (see the approved structure map):
  get_component   Icon.astro imports node:fs — .astro files cannot be served raw.
  find_icon       1173 icons cannot be 1173 resources.
  figma_export    The export is not valid CSS — must be parsed.
  validate_usage  Rebuilt for ui-kit; toafigma's contract describes React props.
"""

from mcp.server.fastmcp import FastMCP

from toa_mcp.loader import RulesLoader
from toa_mcp.settings import Settings
from toa_mcp.tools import adherence, brand, components, figma, icons, infra, standards, styles


def register_all(mcp: FastMCP, loader: RulesLoader, settings: Settings) -> None:
    components.register(mcp, loader)
    icons.register(mcp, loader)
    figma.register(mcp, loader)
    adherence.register(mcp, loader)
    brand.register(mcp, loader, settings)
    infra.register(mcp, loader)
    standards.register(mcp, loader)
    styles.register(mcp, loader)
