"""Auth manager — delegates auth to each provider's CLI."""

from __future__ import annotations

import asyncio

from rich.console import Console

from cli_gateway.adapters.base import InvokeResult
from cli_gateway.models.provider import Provider, ProviderStatus

console = Console()


class AuthManager:
    """Manages authentication flows by delegating to provider CLIs."""

    async def auth(self, provider: Provider) -> InvokeResult:
        """Run the provider's auth commands sequentially."""
        if not provider.auth_commands:
            return InvokeResult(
                success=False,
                error=f"No auth commands configured for {provider.name}",
                exit_code=1,
            )

        console.print(f"[bold blue]Authenticating {provider.display_name}...[/]")

        for cmd in provider.auth_commands:
            console.print(f"[dim]$ {cmd}[/]")
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdin=None,
                stdout=None,
                stderr=None,
            )
            await proc.wait()

            if proc.returncode != 0:
                return InvokeResult(
                    success=False,
                    error=f"Auth command failed: {cmd}",
                    exit_code=proc.returncode or 1,
                    raw_command=cmd,
                )

        console.print(f"[bold green]{provider.display_name} authenticated.[/]")
        return InvokeResult(success=True, raw_command=" && ".join(provider.auth_commands))

    async def check_status(self, provider: Provider) -> ProviderStatus:
        """Check auth status by running the provider's status command."""
        if not provider.status_command:
            return ProviderStatus.INSTALLED

        try:
            proc = await asyncio.create_subprocess_shell(
                provider.status_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
            if proc.returncode == 0:
                output = stdout.decode(errors="replace").lower()
                if "login" in output or "authenticated" in output or "logged in" in output:
                    return ProviderStatus.AUTHENTICATED
                return ProviderStatus.INSTALLED
            return ProviderStatus.INSTALLED
        except (asyncio.TimeoutError, Exception):
            return ProviderStatus.INSTALLED
