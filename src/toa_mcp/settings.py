"""Settings. No rule content lives here — only where to find it."""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TOA_", env_file=".env", extra="ignore")

    rules_path: Path = Field(description="Path to the toa-rules checkout (the data layer).")
    mcp_token: str = Field(description="Bearer token the ASGI middleware validates.")

    # Optional read-only mount of the apps checkout. Deliberately NOT a submodule:
    # a submodule pins a commit, which would freeze the very profile get_app_profile
    # exists to read live. Unset -> the tool fails cleanly with an explanation.
    apps_path: Path | None = Field(
        default=None,
        description="Read-only mount of the apps checkout. Enables get_app_profile.",
    )

    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8000
    mcp_log_level: str = "INFO"

    @field_validator("rules_path")
    @classmethod
    def _must_exist(cls, v: Path) -> Path:
        if not (v / "manifest.json").is_file():
            raise ValueError(f"{v} does not look like a toa-rules checkout (no manifest.json)")
        return v

    @field_validator("mcp_token")
    @classmethod
    def _token_strength(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("TOA_MCP_TOKEN must be at least 32 characters")
        return v
