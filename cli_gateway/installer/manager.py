"""Installer manager — install/update/check underlying CLI tools."""

from __future__ import annotations

import asyncio
import os
import signal
import shutil

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner

from cli_gateway.adapters.base import InvokeResult
from cli_gateway.models.provider import Provider

DEFAULT_INSTALL_TIMEOUT = 180  # 3 minutes

console = Console()


class InstallerManager:
    """Handles installation and version checking for provider CLIs."""

    async def check_installed(self, provider: Provider) -> tuple[bool, str | None]:
        """Check if CLI binary exists on PATH and get version."""
        binary = shutil.which(provider.cli_binary)
        if binary is None:
            return False, None
        try:
            proc = await asyncio.create_subprocess_exec(
                provider.cli_binary,
                provider.version_flag,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            version = stdout.decode().strip() if proc.returncode == 0 else None
            return True, version
        except Exception:
            return True, None

    async def install(
        self, provider: Provider, timeout: int = DEFAULT_INSTALL_TIMEOUT
    ) -> InvokeResult:
        """Run the provider's install command with timeout and progress."""
        console.print(f"[bold blue]Installing {provider.display_name}...[/]")
        console.print(f"[dim]$ {provider.install_command}[/]")
        console.print(f"[dim]Timeout: {timeout}s[/]")

        proc: asyncio.subprocess.Process | None = None
        try:
            proc = await asyncio.create_subprocess_shell(
                provider.install_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            with Live(
                Spinner("dots", text=f"Installing {provider.display_name}..."),
                console=console,
                refresh_per_second=4,
            ):
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )

            success = proc.returncode == 0
            if success:
                console.print(f"[bold green]{provider.display_name} installed successfully.[/]")
            else:
                console.print(f"[bold red]Installation failed (exit {proc.returncode}).[/]")
                err = stderr.decode(errors="replace").strip()
                if err:
                    console.print(f"[red]{err}[/]")

            return InvokeResult(
                success=success,
                output=stdout.decode(errors="replace").strip(),
                error=stderr.decode(errors="replace").strip(),
                exit_code=proc.returncode or 0,
                raw_command=provider.install_command,
            )
        except asyncio.TimeoutError:
            self._kill_process(proc)
            console.print(
                f"[bold red]Installation timed out after {timeout}s — process killed.[/]"
            )
            console.print("[yellow]Tip: retry with a longer timeout via --timeout[/]")
            return InvokeResult(
                success=False,
                error=f"Installation timed out after {timeout}s",
                exit_code=-1,
                raw_command=provider.install_command,
            )
        except Exception as e:
            self._kill_process(proc)
            return InvokeResult(
                success=False,
                error=str(e),
                exit_code=-1,
                raw_command=provider.install_command,
            )

    @staticmethod
    def _kill_process(proc: asyncio.subprocess.Process | None) -> None:
        """Kill a subprocess and its entire process group."""
        if proc is None or proc.returncode is not None:
            return
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except (ProcessLookupError, OSError):
            try:
                proc.kill()
            except ProcessLookupError:
                pass

    async def check_all(
        self, providers: dict[str, Provider]
    ) -> dict[str, tuple[bool, str | None]]:
        """Check installation status for all providers concurrently."""
        tasks = {
            name: self.check_installed(prov) for name, prov in providers.items()
        }
        results = await asyncio.gather(*tasks.values())
        return dict(zip(tasks.keys(), results))
