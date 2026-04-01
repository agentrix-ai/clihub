"""Provider configuration model."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ProviderStatus(str, Enum):
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    AUTHENTICATED = "authenticated"


class Provider(BaseModel):
    """Metadata for a single CLI provider (e.g. lark, dingtalk, wecom)."""

    name: str = Field(description="Short identifier: wecom / dingtalk / lark")
    display_name: str = ""
    cli_binary: str = Field(description="Binary name on PATH, e.g. 'lark-cli'")
    install_command: str = Field(
        description="Shell command to install, e.g. 'npm install -g @larksuite/cli'"
    )
    auth_commands: list[str] = Field(
        default_factory=list,
        description="Commands to run for auth, e.g. ['lark-cli config init', 'lark-cli auth login --recommend']",
    )
    status_command: str = Field(
        default="",
        description="Command to check auth status, e.g. 'lark-cli auth status'",
    )
    schema_command: str = Field(
        default="",
        description="Command to fetch schema, e.g. 'lark-cli schema'",
    )
    version_flag: str = "--version"
    homepage: str = ""
    description: str = ""
