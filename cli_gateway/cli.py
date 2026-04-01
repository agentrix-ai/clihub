"""Main CLI command definitions — the single entry point for cli-hub."""

from __future__ import annotations

import asyncio
import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from cli_gateway import __version__
from cli_gateway.auth.manager import AuthManager
from cli_gateway.core.dispatcher import Dispatcher
from cli_gateway.core.registry import get_registry
from cli_gateway.core.search import search_operations
from cli_gateway.installer.manager import InstallerManager

app = typer.Typer(
    name="cli-hub",
    help="Unified CLI gateway for enterprise platforms — search, install, auth and invoke WeCom / DingTalk / Lark CLIs.",
    no_args_is_help=True,
)
console = Console()


def _run(coro):
    """Run an async coroutine from sync typer context."""
    return asyncio.run(coro)


_BUILTIN_ADAPTERS = {"wecom", "dingtalk", "lark"}


def _get_dispatcher() -> Dispatcher:
    from cli_gateway.adapters.dingtalk import DingTalkAdapter
    from cli_gateway.adapters.generic import GenericAdapter, InvokeStyle
    from cli_gateway.adapters.lark import LarkAdapter
    from cli_gateway.adapters.wecom import WeComAdapter

    registry = get_registry()
    dispatcher = Dispatcher(registry)

    for name, provider in registry.providers.items():
        if name == "wecom":
            dispatcher.register_adapter(name, WeComAdapter(provider))
        elif name == "dingtalk":
            dispatcher.register_adapter(name, DingTalkAdapter(provider))
        elif name == "lark":
            dispatcher.register_adapter(name, LarkAdapter(provider))
        else:
            dispatcher.register_adapter(name, GenericAdapter(provider, InvokeStyle.FLAGS))

    return dispatcher


# ── search ───────────────────────────────────────────────

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query (Chinese or English)"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider: wecom/dingtalk/lark"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category: calendar/todo/msg/..."),
    top: int = typer.Option(10, "--top", "-n", help="Number of results"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Search tools across all providers by keyword or description."""
    registry = get_registry()
    results = search_operations(
        query, registry.operations, provider=provider, category=category, top_k=top
    )

    if not results:
        console.print("[yellow]No matching tools found.[/]")
        raise typer.Exit(1)

    if output_json:
        out = [
            {
                "id": op.id,
                "description": op.description,
                "score": round(score, 3),
                "example": op.example,
                "input_schema": op.input_schema,
            }
            for op, score in results
        ]
        console.print_json(json.dumps(out, ensure_ascii=False))
        return

    table = Table(title=f"Search results for: {query}", show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Example", style="dim")
    table.add_column("Score", style="yellow", justify="right")

    for op, score in results:
        table.add_row(op.id, op.description, op.example or "-", f"{score:.2f}")

    console.print(table)
    console.print("\n[dim]Tip: run [bold]cli-hub info <ID>[/bold] to see full parameter schema.[/]")


# ── info ─────────────────────────────────────────────────

@app.command()
def info(
    operation_id: str = typer.Argument(..., help="Operation ID, e.g. lark.calendar.agenda"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """Show full details and parameter schema for a tool."""
    registry = get_registry()
    op = registry.get_operation(operation_id)

    if op is None:
        console.print(f"[red]Operation not found: {operation_id}[/]")
        console.print("[dim]Use [bold]cli-hub search <query>[/bold] to find tools.[/]")
        raise typer.Exit(1)

    if output_json:
        console.print_json(json.dumps(op.model_dump(), ensure_ascii=False))
        return

    console.print(f"\n[bold cyan]{op.id}[/]")
    console.print(f"  [white]{op.description}[/]")
    if op.description_en:
        console.print(f"  [dim]{op.description_en}[/]")

    console.print(f"\n  Provider:  [green]{op.provider}[/]")
    console.print(f"  Category:  [green]{op.category}[/]")

    if op.example:
        console.print(f"\n  [bold]Example:[/]")
        console.print(f"  [dim]$ {op.example}[/]")

    if op.argv_template:
        console.print(f"\n  [bold]Command template:[/]")
        console.print(f"  [dim]{' '.join(op.argv_template)}[/]")

    if op.input_schema:
        console.print(f"\n  [bold]Parameters:[/]")
        props = op.input_schema.get("properties", {})
        required = set(op.input_schema.get("required", []))
        for param_name, param_def in props.items():
            req_mark = "[red]*[/]" if param_name in required else " "
            param_type = param_def.get("type", "any")
            param_desc = param_def.get("description", "")
            console.print(f"    {req_mark} [cyan]{param_name}[/] ({param_type}) {param_desc}")
        if required:
            console.print(f"\n  [dim][red]*[/] = required[/]")
    else:
        console.print(f"\n  [dim]No parameter schema available. Refer to the example above.[/]")

    console.print(f"\n  [bold]Run:[/]")
    if op.provider == "wecom":
        console.print(f'  [dim]$ cli-hub run {op.id} \'{{...}}\'[/]')
    else:
        console.print(f"  [dim]$ cli-hub run {op.id} --param value[/]")
    console.print()


# ── install ──────────────────────────────────────────────

@app.command()
def install(
    provider_name: Optional[str] = typer.Argument(None, help="Provider to install: wecom/dingtalk/lark"),
    all_providers: bool = typer.Option(False, "--all", help="Install all providers"),
    timeout: int = typer.Option(180, "--timeout", "-t", help="Timeout in seconds (default 180)"),
):
    """Install underlying CLI tools."""
    registry = get_registry()
    installer = InstallerManager()

    if all_providers:
        targets = list(registry.providers.values())
    elif provider_name:
        prov = registry.get_provider(provider_name)
        if prov is None:
            console.print(f"[red]Unknown provider: {provider_name}[/]")
            console.print(f"Available: {', '.join(registry.providers.keys())}")
            raise typer.Exit(1)
        targets = [prov]
    else:
        console.print("[yellow]Specify a provider or use --all[/]")
        console.print(f"Available: {', '.join(registry.providers.keys())}")
        raise typer.Exit(1)

    async def _do():
        for prov in targets:
            installed, ver = await installer.check_installed(prov)
            if installed:
                console.print(f"[green]{prov.display_name} already installed ({ver or 'version unknown'}).[/]")
                continue
            result = await installer.install(prov, timeout=timeout)
            if not result.success:
                console.print(f"[red]Failed to install {prov.display_name}: {result.error}[/]")

    _run(_do())


# ── auth ─────────────────────────────────────────────────

@app.command()
def auth(
    provider_name: Optional[str] = typer.Argument(None, help="Provider to authenticate: wecom/dingtalk/lark"),
    status: bool = typer.Option(False, "--status", "-s", help="Show auth status for all providers"),
):
    """Authenticate with a provider or check auth status."""
    registry = get_registry()
    auth_mgr = AuthManager()
    installer = InstallerManager()

    if status or provider_name is None:
        async def _show_status():
            install_status = await installer.check_all(registry.providers)
            table = Table(title="Provider Status")
            table.add_column("Provider", style="cyan")
            table.add_column("Installed", style="green")
            table.add_column("Version", style="white")
            table.add_column("Auth", style="yellow")

            for name, prov in registry.providers.items():
                installed, ver = install_status[name]
                if not installed:
                    table.add_row(prov.display_name, "[red]No[/]", "-", "-")
                else:
                    auth_st = await auth_mgr.check_status(prov)
                    auth_icon = "[green]Yes[/]" if auth_st.value == "authenticated" else "[yellow]?[/]"
                    table.add_row(prov.display_name, "[green]Yes[/]", ver or "?", auth_icon)

            console.print(table)

        _run(_show_status())
        return

    prov = registry.get_provider(provider_name)
    if prov is None:
        console.print(f"[red]Unknown provider: {provider_name}[/]")
        console.print(f"Available: {', '.join(registry.providers.keys())}")
        raise typer.Exit(1)

    async def _do_auth():
        installed, _ = await installer.check_installed(prov)
        if not installed:
            console.print(f"[red]{prov.display_name} is not installed.[/]")
            console.print(f"Run first: [bold]cli-hub install {provider_name}[/]")
            raise typer.Exit(1)
        await auth_mgr.auth(prov)

    _run(_do_auth())


# ── run ──────────────────────────────────────────────────

@app.command(
    context_settings={"allow_extra_args": True, "allow_interspersed_args": True},
)
def run(
    ctx: typer.Context,
    operation_id: str = typer.Argument(..., help="Operation ID, e.g. lark.calendar.agenda"),
    args: Optional[str] = typer.Option(None, "--args", "-a", help="JSON arguments string"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Force JSON output"),
):
    """Run a specific operation by its fully-qualified ID.

    \b
    Two ways to pass arguments:
      JSON:  cli-hub run wecom.msg.send_message --args '{"chat_type":1,"chatid":"user1"}'
      Flags: cli-hub run lark.im.messages_send --chat-id oc_xxx --text Hello
    """
    parsed_args: dict | None = None

    if args:
        try:
            parsed_args = json.loads(args)
        except json.JSONDecodeError:
            console.print(f"[red]Invalid JSON: {args}[/]")
            raise typer.Exit(1)
    elif ctx.args:
        parsed_args = _parse_extra_args(ctx.args)

    dispatcher = _get_dispatcher()

    async def _do():
        result = await dispatcher.invoke(operation_id, parsed_args)
        if result.success:
            if output_json:
                try:
                    data = json.loads(result.output)
                    console.print_json(json.dumps(data, ensure_ascii=False))
                except json.JSONDecodeError:
                    console.print(result.output)
            else:
                console.print(result.output)
        else:
            console.print(f"[red]Error:[/] {result.error}")
            if result.output:
                console.print(result.output)
            raise typer.Exit(result.exit_code)

    _run(_do())


def _parse_extra_args(extra: list[str]) -> dict:
    """Parse --key value pairs from extra args into a dict."""
    result: dict = {}
    i = 0
    while i < len(extra):
        arg = extra[i]
        if arg.startswith("--"):
            key = arg[2:]
            if i + 1 < len(extra) and not extra[i + 1].startswith("--"):
                value = extra[i + 1]
                try:
                    result[key] = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    result[key] = value
                i += 2
            else:
                result[key] = True
                i += 1
        else:
            try:
                return json.loads(arg)
            except (json.JSONDecodeError, ValueError):
                i += 1
    return result


# ── list ─────────────────────────────────────────────────

@app.command(name="list")
def list_cmd(
    provider_name: Optional[str] = typer.Argument(None, help="Provider to list tools for"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    output_json: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
):
    """List providers and their available tools."""
    registry = get_registry()

    if provider_name is None:
        if output_json:
            data = [
                {"name": p.name, "display_name": p.display_name, "description": p.description,
                 "tools_count": len(registry.list_operations(provider=p.name))}
                for p in registry.providers.values()
            ]
            console.print_json(json.dumps(data, ensure_ascii=False))
            return

        table = Table(title="Available Providers")
        table.add_column("Name", style="cyan")
        table.add_column("Display Name", style="white")
        table.add_column("Tools", style="green", justify="right")
        table.add_column("Description", style="dim")

        for prov in registry.providers.values():
            count = len(registry.list_operations(provider=prov.name))
            table.add_row(prov.name, prov.display_name, str(count), prov.description)

        console.print(table)
        return

    ops = registry.list_operations(provider=provider_name, category=category)
    if not ops:
        console.print(f"[yellow]No tools found for {provider_name}" +
                       (f" / {category}" if category else "") + "[/]")
        raise typer.Exit(1)

    if output_json:
        data = [{"id": o.id, "description": o.description, "category": o.category} for o in ops]
        console.print_json(json.dumps(data, ensure_ascii=False))
        return

    table = Table(title=f"Tools: {provider_name}" + (f" / {category}" if category else ""))
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Category", style="green")
    table.add_column("Description", style="white")

    for op in ops:
        table.add_row(op.id, op.category, op.description)

    console.print(table)


# ── doctor ───────────────────────────────────────────────

@app.command()
def doctor():
    """Check installation and auth status for all providers."""
    registry = get_registry()
    installer = InstallerManager()
    auth_mgr = AuthManager()

    async def _do():
        console.print("[bold]CLI Hub Doctor[/]\n")

        install_status = await installer.check_all(registry.providers)

        all_ok = True
        for name, prov in registry.providers.items():
            installed, ver = install_status[name]
            if installed:
                auth_st = await auth_mgr.check_status(prov)
                auth_str = "[green]authenticated[/]" if auth_st.value == "authenticated" else "[yellow]unknown[/]"
                console.print(f"  [green]OK[/]  {prov.display_name}: v{ver or '?'}, auth: {auth_str}")
            else:
                all_ok = False
                console.print(f"  [red]--[/]  {prov.display_name}: [red]not installed[/]")
                console.print(f"       Install: [dim]{prov.install_command}[/]")

        ops_count = len(registry.operations)
        console.print(f"\n  Schema: [cyan]{ops_count}[/] operations loaded")

        if all_ok:
            console.print("\n[bold green]All providers OK.[/]")
        else:
            console.print("\n[yellow]Some providers are missing. Run: cli-hub install --all[/]")

    _run(_do())


# ── refresh ──────────────────────────────────────────────

@app.command()
def refresh(
    provider_name: Optional[str] = typer.Argument(None, help="Provider to refresh schema for"),
    remote: bool = typer.Option(True, "--remote/--no-remote", help="Pull latest schemas from clihub.cc (default: on)"),
):
    """Refresh tool schemas — pull from remote registry + reload local + extract dynamic schemas."""
    from pathlib import Path
    from cli_gateway.core.registry import REMOTE_REGISTRY_URL, _LOCAL_CACHE_DIR

    if remote:
        _pull_remote_schemas(REMOTE_REGISTRY_URL, _LOCAL_CACHE_DIR, provider_name)

    dispatcher = _get_dispatcher()
    registry = get_registry()

    registry.load()
    static_count = len(registry.operations)
    console.print(f"[green]Loaded {static_count} operations from schemas.[/]")

    async def _do():
        targets = [provider_name] if provider_name else list(registry.providers.keys())
        for name in targets:
            adapter = dispatcher.get_adapter(name)
            if adapter is None:
                continue
            installed, _ = await adapter.is_installed()
            if not installed:
                console.print(f"[yellow]{name}: not installed, skipping dynamic extraction.[/]")
                continue
            console.print(f"[blue]Extracting dynamic schema for {name}...[/]")
            ops = await adapter.refresh_schema()
            if ops:
                registry.add_operations(ops)
                console.print(f"  [green]+{len(ops)} operations from {name} CLI[/]")

        console.print(f"\n[green]Total: {len(registry.operations)} operations[/]")

    _run(_do())


def _pull_remote_schemas(url: str, cache_dir: Path, provider_name: str | None = None):
    """Pull schemas from remote registry and save to local cache."""
    import httpx
    from rich.progress import Progress, SpinnerColumn, TextColumn

    with Progress(SpinnerColumn(), TextColumn("[bold blue]{task.description}"), console=console) as progress:
        task = progress.add_task("Pulling schemas from clihub.cc...", total=None)
        try:
            with httpx.Client(timeout=15) as client:
                if provider_name:
                    resp = client.get(f"{url}/{provider_name}")
                    resp.raise_for_status()
                    schemas = {provider_name: resp.json()}
                else:
                    resp = client.get(url)
                    resp.raise_for_status()
                    schemas = resp.json()

            cache_dir.mkdir(parents=True, exist_ok=True)
            for name, data in schemas.items():
                path = cache_dir / f"{name}.json"
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

            progress.update(task, description=f"[green]Pulled {len(schemas)} schema(s) from remote registry.[/]")
        except Exception as e:
            progress.update(task, description=f"[yellow]Remote pull failed ({e}), using local schemas.[/]")


# ── add ──────────────────────────────────────────────────

@app.command()
def add(
    binary: str = typer.Argument(..., help="CLI binary name, e.g. 'meitu-cli'"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Provider short name (default: binary without -cli suffix)"),
    display_name: Optional[str] = typer.Option(None, "--display", "-d", help="Display name, e.g. 'MeiTu (美图)'"),
    install_cmd: Optional[str] = typer.Option(None, "--install-cmd", help="Install command"),
    auth_cmd: Optional[str] = typer.Option(None, "--auth-cmd", help="Auth command"),
    schema_cmd: Optional[str] = typer.Option(None, "--schema-cmd", help="Schema command for auto-extraction"),
    invoke_style: str = typer.Option("flags", "--style", help="Invoke style: 'flags' (--key val) or 'json_arg' (JSON string)"),
):
    """Add a new CLI provider and auto-extract its tool schema.

    \b
    Examples:
      cli-hub add meitu-cli --display "MeiTu (美图)" --install-cmd "npm i -g @meitu/cli"
      cli-hub add gaode --schema-cmd "gaode schema" --style flags
    """
    from pathlib import Path
    from cli_gateway.core.schema_extractor import auto_extract, save_schema
    from cli_gateway.models.provider import Provider

    prov_name = name or binary.replace("-cli", "").replace("_cli", "").replace("-", "_")

    registry = get_registry()
    if registry.get_provider(prov_name):
        console.print(f"[yellow]Provider '{prov_name}' already exists. Use --name to choose a different name.[/]")
        raise typer.Exit(1)

    provider = Provider(
        name=prov_name,
        display_name=display_name or prov_name,
        cli_binary=binary,
        install_command=install_cmd or f"echo 'Please install {binary} manually'",
        auth_commands=[auth_cmd] if auth_cmd else [],
        schema_command=schema_cmd or "",
    )

    async def _do():
        installed, ver = await InstallerManager().check_installed(provider)
        if not installed:
            console.print(f"[yellow]{binary} not found on PATH.[/]")
            console.print(f"[dim]Will attempt to extract schema from --help if available after install.[/]")

        console.print(f"[blue]Auto-extracting schema for {binary}...[/]")
        ops = await auto_extract(provider)

        if ops:
            schemas_dir = Path(__file__).resolve().parent / "schemas"
            path = save_schema(prov_name, ops, schemas_dir)
            console.print(f"  [green]{len(ops)} operations extracted → {path}[/]")
        else:
            console.print(f"  [yellow]No operations extracted. You can manually create schemas/{prov_name}.json[/]")

        registry.register_provider(provider)
        if ops:
            registry.add_operations(ops)

        console.print(f"\n[bold green]Provider '{prov_name}' added![/]")
        console.print(f"  [dim]Binary:  {binary}[/]")
        console.print(f"  [dim]Tools:   {len(ops)}[/]")
        console.print(f"  [dim]Style:   {invoke_style}[/]")
        console.print(f"\n[dim]Try: cli-hub list {prov_name}[/]")

    _run(_do())


# ── version ──────────────────────────────────────────────

@app.command()
def version():
    """Show cli-hub version."""
    console.print(f"cli-hub v{__version__}")
