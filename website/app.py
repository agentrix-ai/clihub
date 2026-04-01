"""clihub.cc — Landing page + Schema Registry API."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
SCHEMAS_DIR = BASE_DIR / "schemas"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="clihub.cc",
    description="Schema Registry & Landing Page for cli-hub",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# In-memory schema cache
_cache: dict[str, Any] = {}
_cache_mtime: dict[str, float] = {}


def _load_schema(name: str) -> dict | None:
    """Load a single schema JSON, with mtime-based cache invalidation."""
    path = SCHEMAS_DIR / f"{name}.json"
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    if name in _cache and _cache_mtime.get(name) == mtime:
        return _cache[name]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        _cache[name] = data
        _cache_mtime[name] = mtime
        return data
    except (json.JSONDecodeError, OSError):
        return None


def _load_all_schemas() -> dict[str, dict]:
    """Load all schema files from disk."""
    result = {}
    if not SCHEMAS_DIR.exists():
        return result
    for f in sorted(SCHEMAS_DIR.glob("*.json")):
        if f.stem == "providers":
            continue
        data = _load_schema(f.stem)
        if data is not None:
            result[f.stem] = data
    return result


def _build_provider_summary(schemas: dict[str, dict]) -> list[dict]:
    """Build provider summary with tool counts from loaded schemas."""
    providers_file = SCHEMAS_DIR / "providers.json"
    meta: dict[str, dict] = {}
    if providers_file.exists():
        try:
            meta_list = json.loads(providers_file.read_text(encoding="utf-8"))
            meta = {p["name"]: p for p in meta_list}
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    summaries = []
    for name, schema in schemas.items():
        ops = schema.get("operations", [])
        info = meta.get(name, {})
        summaries.append({
            "name": name,
            "display_name": info.get("display_name", name),
            "description": info.get("description", ""),
            "homepage": info.get("homepage", ""),
            "tools_count": len(ops),
            "categories": sorted({op.get("category", "") for op in ops} - {""}),
        })
    return summaries


# ── Routes ────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    schemas = _load_all_schemas()
    providers = _build_provider_summary(schemas)
    total_tools = sum(p["tools_count"] for p in providers)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "providers": providers,
            "total_tools": total_tools,
            "provider_count": len(providers),
            "version": "0.2.0",
        },
    )


@app.get("/api/providers")
async def api_providers():
    schemas = _load_all_schemas()
    return _build_provider_summary(schemas)


@app.get("/api/schemas")
async def api_schemas_all():
    """Return all schemas — used by `cli-hub refresh --remote`."""
    schemas = _load_all_schemas()
    return schemas


@app.get("/api/schemas/{provider}")
async def api_schema_single(provider: str):
    data = _load_schema(provider)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Schema not found: {provider}")
    return data


@app.get("/api/version")
async def api_version():
    """Schema registry version, based on newest file mtime."""
    if not SCHEMAS_DIR.exists():
        return {"version": "0", "updated_at": 0}
    files = list(SCHEMAS_DIR.glob("*.json"))
    if not files:
        return {"version": "0", "updated_at": 0}
    latest = max(f.stat().st_mtime for f in files)
    return {
        "version": str(int(latest)),
        "updated_at": int(latest),
        "schema_count": len([f for f in files if f.stem != "providers"]),
    }


@app.get("/health")
async def health():
    schemas = _load_all_schemas()
    return {
        "status": "ok",
        "schemas": len(schemas),
        "total_operations": sum(
            len(s.get("operations", [])) for s in schemas.values()
        ),
    }
