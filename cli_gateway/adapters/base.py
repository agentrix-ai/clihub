"""Abstract adapter interface — every provider implements this."""

from __future__ import annotations

import asyncio
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from cli_gateway.models.operation import Operation
from cli_gateway.models.provider import Provider, ProviderStatus


@dataclass
class InvokeResult:
    success: bool
    output: str = ""
    error: str = ""
    exit_code: int = 0
    raw_command: str = ""


class AbstractAdapter(ABC):
    """Base class all provider adapters inherit from."""

    def __init__(self, provider: Provider) -> None:
        self.provider = provider
        self._operations: list[Operation] = []

    # ── install ──────────────────────────────────────────

    async def is_installed(self) -> tuple[bool, str | None]:
        """Check if the CLI binary is on PATH; return (ok, version)."""
        binary = shutil.which(self.provider.cli_binary)
        if binary is None:
            return False, None
        try:
            proc = await asyncio.create_subprocess_exec(
                self.provider.cli_binary,
                self.provider.version_flag,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            version = stdout.decode().strip() if proc.returncode == 0 else None
            return True, version
        except Exception:
            return True, None

    @abstractmethod
    async def install(self) -> InvokeResult:
        """Install the underlying CLI tool."""

    # ── auth ─────────────────────────────────────────────

    @abstractmethod
    async def auth(self, profile: str | None = None) -> InvokeResult:
        """Run the provider's auth / login flow."""

    @abstractmethod
    async def auth_status(self) -> ProviderStatus:
        """Return current authentication status."""

    # ── operations / schema ──────────────────────────────

    def set_operations(self, ops: list[Operation]) -> None:
        self._operations = ops

    def get_operations(self) -> list[Operation]:
        return list(self._operations)

    @abstractmethod
    async def refresh_schema(self) -> list[Operation]:
        """Dynamically fetch schema from the CLI (if supported)."""

    # ── invoke ───────────────────────────────────────────

    @abstractmethod
    async def invoke(self, operation: Operation, args: dict | None = None) -> InvokeResult:
        """Execute a single operation and return structured result."""

    # ── helpers ──────────────────────────────────────────

    async def _run_shell(self, cmd: str, timeout: float = 120) -> InvokeResult:
        """Run a shell command and capture output."""
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return InvokeResult(
                success=proc.returncode == 0,
                output=stdout.decode(errors="replace").strip(),
                error=stderr.decode(errors="replace").strip(),
                exit_code=proc.returncode or 0,
                raw_command=cmd,
            )
        except asyncio.TimeoutError:
            return InvokeResult(
                success=False,
                error=f"Command timed out after {timeout}s",
                raw_command=cmd,
                exit_code=-1,
            )
        except Exception as e:
            return InvokeResult(
                success=False,
                error=str(e),
                raw_command=cmd,
                exit_code=-1,
            )
