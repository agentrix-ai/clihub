"""Schema extractor — auto-generate schemas from CLI introspection.

Three extraction strategies (no LLM required):
  1. `schema` command  → parse JSON output directly (dingtalk/lark)
  2. `--help` recursive → parse subcommands and flags via regex
  3. Manual / LLM-assisted → for CLIs without structured output (wecom)
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from cli_gateway.models.operation import Operation
from cli_gateway.models.provider import Provider


async def _run(cmd: str, timeout: float = 30) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode or 0, stdout.decode(errors="replace"), stderr.decode(errors="replace")
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "timeout"


# ── Strategy 1: schema command ───────────────────────────

async def extract_from_schema_command(provider: Provider) -> list[Operation]:
    """Extract operations from `<cli> schema` JSON output."""
    if not provider.schema_command:
        return []

    code, stdout, _ = await _run(provider.schema_command)
    if code != 0 or not stdout.strip():
        return []

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return []

    ops: list[Operation] = []
    products = data.get("products", data.get("services", []))
    for product in products:
        pid = product.get("id", product.get("name", ""))
        tools = product.get("tools", product.get("commands", []))
        for tool in tools:
            tname = tool.get("name", tool.get("id", ""))
            ops.append(Operation(
                id=f"{provider.name}.{pid}.{tname}",
                provider=provider.name,
                category=pid,
                name=tname,
                description=tool.get("description", ""),
                description_en=tool.get("description_en", tool.get("description", "")),
                keywords=[pid, tname],
                argv_template=tool.get("argv", []),
                input_schema=tool.get("parameters"),
                example=tool.get("example", ""),
            ))
    return ops


# ── Strategy 2: --help recursive parsing ─────────────────

_SUBCMD_RE = re.compile(r"^\s{2,4}(\S+)\s{2,}", re.MULTILINE)
_FLAG_RE = re.compile(
    r"--(\S+?)(?:\s+<(\w+)>|\s+(\w+))?\s{2,}(.+)",
    re.MULTILINE,
)
_REQUIRED_RE = re.compile(r"\[required\]", re.IGNORECASE)


async def extract_from_help(provider: Provider, max_depth: int = 3) -> list[Operation]:
    """Recursively parse `<cli> [subcommand...] --help` to discover tools."""
    binary = provider.cli_binary
    ops: list[Operation] = []
    await _recurse_help(binary, [], provider.name, ops, max_depth)
    return ops


async def _recurse_help(
    binary: str,
    path: list[str],
    provider_name: str,
    ops: list[Operation],
    depth: int,
) -> None:
    if depth <= 0:
        return

    cmd = f"{binary} {' '.join(path)} --help" if path else f"{binary} --help"
    code, stdout, _ = await _run(cmd, timeout=10)
    if code != 0:
        return

    subcmds = _parse_subcommands(stdout)
    flags = _parse_flags(stdout)

    if flags and not subcmds:
        category = path[0] if path else "general"
        name = "_".join(path[1:]) if len(path) > 1 else (path[0] if path else binary)
        desc_match = re.search(r"^\s*(.+?)(?:\n|$)", stdout)
        desc = desc_match.group(1).strip() if desc_match else ""

        schema = _flags_to_schema(flags) if flags else None
        argv = [binary] + path

        ops.append(Operation(
            id=f"{provider_name}.{category}.{name}",
            provider=provider_name,
            category=category,
            name=name,
            description=desc,
            argv_template=argv,
            input_schema=schema,
            keywords=[category, name],
        ))
        return

    skip = {"help", "version", "init", "completion"}
    for sub_name, sub_desc in subcmds:
        if sub_name.lower() in skip:
            continue
        await _recurse_help(binary, path + [sub_name], provider_name, ops, depth - 1)


def _parse_subcommands(help_text: str) -> list[tuple[str, str]]:
    """Extract subcommand names and descriptions from --help output."""
    results = []
    in_commands = False
    for line in help_text.split("\n"):
        lower = line.lower().strip()
        if lower.startswith("commands:") or lower.startswith("subcommands:"):
            in_commands = True
            continue
        if in_commands:
            if not line.strip():
                if results:
                    break
                continue
            match = re.match(r"^\s{2,}(\S+)\s{2,}(.*)$", line)
            if match:
                results.append((match.group(1).strip(), match.group(2).strip()))
            elif line.strip() and not line.startswith(" "):
                break
    return results


def _parse_flags(help_text: str) -> list[dict]:
    """Extract --flag definitions from --help output."""
    flags = []
    for match in _FLAG_RE.finditer(help_text):
        name = match.group(1).rstrip(",")
        if name in ("help", "version"):
            continue
        type_hint = match.group(2) or match.group(3) or "string"
        desc = match.group(4).strip()
        required = bool(_REQUIRED_RE.search(desc))
        flags.append({
            "name": name,
            "type": _normalize_type(type_hint),
            "description": desc,
            "required": required,
        })
    return flags


def _normalize_type(t: str) -> str:
    t = t.lower()
    if t in ("int", "integer", "number"):
        return "integer"
    if t in ("bool", "boolean", "flag"):
        return "boolean"
    if t in ("float", "double"):
        return "number"
    return "string"


def _flags_to_schema(flags: list[dict]) -> dict:
    """Convert parsed flags into JSON Schema."""
    props = {}
    required = []
    for f in flags:
        props[f["name"]] = {
            "type": f["type"],
            "description": f["description"],
        }
        if f["required"]:
            required.append(f["name"])
    schema: dict = {"type": "object", "properties": props}
    if required:
        schema["required"] = required
    return schema


# ── Combine & Save ───────────────────────────────────────

async def auto_extract(provider: Provider) -> list[Operation]:
    """Try schema command first, fall back to --help parsing."""
    ops = await extract_from_schema_command(provider)
    if ops:
        return ops
    return await extract_from_help(provider)


def save_schema(provider_name: str, operations: list[Operation], output_dir: Path) -> Path:
    """Save extracted operations to a JSON schema file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{provider_name}.json"
    data = {
        "provider": provider_name,
        "version": "auto",
        "operations": [op.model_dump(exclude_none=True) for op in operations],
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
