# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A FastAPI + HTMX dashboard that visualizes factory equipment run status on a floor-map-style canvas (装置の稼働状態可視化). Equipment shapes are drawn directly on a fixed white canvas and colored by status (running / stopped / alarm); layouts are editable via drag-and-resize. Multiple named canvases ("キャンバス", e.g. per floor or per room) are supported, switchable from the dashboard.

**Hard constraint: this app must never talk to a database directly.** Data comes either from local JSON files (current "offline/standalone" mode) or, in the future, from an external backend's REST API ("online" mode). If you're tempted to add a DB driver or ORM, stop — that always belongs on the other side of a REST API this app calls, not in this repo.

## Commands

All Python commands run from `app/` (it is the Poetry project root itself, not a package inside it — internal imports are bare, e.g. `from routes import api, ui`, no `app.` prefix).

```bash
cd app
poetry install                 # install deps (add --with dev for lint/type/test tools)
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000   # dev server
poetry run ruff check .        # lint
poetry run ruff format .       # format
poetry run mypy .              # type check
poetry run pytest              # tests (no tests/ directory exists yet)
```

Docker (multi-stage UBI9 build: `base` → `dependencies` → `dev`/`prd`):

```bash
docker compose up -d                                            # dev target, uses compose.override.yaml
docker compose -f compose.yaml -f compose.production.yaml up -d --build   # prd target, port 8888
```

Compose files intentionally follow the Compose Specification naming (`compose.yaml` / `compose.override.yaml` / `compose.production.yaml`) — no `docker-` prefix, no mixed extensions. Keep this naming if adding more override files.

## Architecture

**Layering**: `routes/` → `services/` → `providers/` → `schemas/`.

- `routes/ui.py` — HTMX/page routes, returns `Jinja2Templates` `HTMLResponse`s (both full pages and `partials/*` fragments for HTMX swaps).
- `routes/api.py` — JSON API under the `/api` prefix: export endpoints (`GET /api/standalone/layout/export`, `GET /api/standalone/status/export`) and `POST /api/layouts/save` (used by the layout editor's direct save button).
- `services/` — business logic (`layout_service`, `status_service`, `import_export_service`). No I/O of their own; they call into `providers/`.
- `providers/json_status_provider.py` — the only place that touches the filesystem for layout/status data. `JsonStatusProvider` reads/writes `data/sample/layouts/<id>/layout.json` and the single global `data/sample/status.json`.
- `schemas/` — Pydantic v2 models. JSON on disk/wire is camelCase; Python is snake_case, bridged via `Field(alias=...)` + `ConfigDict(populate_by_name=True)` (e.g. `tag_id: str = Field(alias="tagId")`).

**Data model**: layouts are per-canvas (`layouts/<layout_id>/layout.json`: shapes, position/size, and each item's `tagId`). Status is a *single global* file (`status.json`) keyed by `tagId`, not per-canvas — `status_service.get_dashboard(layout_id)` loads the layout, loads the whole status snapshot, and joins them in memory by `tag_id`. This mirrors the eventual real backend's single `status_cache` design, so keep status global if you extend it.

**Persistence model (offline/standalone mode)**: writes go straight to those JSON files on local disk — no external volume, no DB. This is deliberate: the container is disposable (rebuilding it resets to the sample data), because durable storage is expected to live behind the future online backend, not in this app. Don't add volume mounts or a DB "to fix" that; it's the intended lifecycle. The two-step **validate → confirm-save** pattern (`POST .../import` returns a preview + a confirm form, `POST .../import/confirm` actually persists) is used for both layout and status imports on the Offline設定 (standalone) screen — follow it if adding another importable resource, matching by `id` for layouts (new vs. overwrite) since status has no per-record id.

**Online mode (not yet implemented)**: `repositories/*.py`, `providers/api_status_provider.py`, `schemas/api_config.py`, and `templates/partials/api_source_detail.html` are empty scaffold files reserved for the future REST-API-backed data source. `operation_mode` (`online`/`offline`, a cookie) already exists as a UI toggle, but nothing switches provider behavior on it yet — `JsonStatusProvider` is used unconditionally today. When implementing online mode, add an API-backed provider behind the same interface `JsonStatusProvider` exposes (`list_layouts`, `load_layout`, `save_layout`, `load_status`, `save_status`) and switch on `operation_mode` at the service layer — never let a route or template reach past `services/` into a provider directly.

**Settings**: persisted as cookies (`theme`, `operation_mode`, `default_layout_id`, `default_refresh_interval`), not a DB — validated server-side in `routes/ui.py` with fallback to defaults on any invalid/missing value.

**Frontend**: server-rendered Jinja2 + HTMX, no build step. `static/js/htmx.min.js` is vendored (not a CDN) intentionally — this fits the factory-floor offline-network use case as well as this sandbox's blocked CDN access. Dashboard auto-refresh (`static/js/dashboard.js`) drives HTMX manually via a `setInterval` calling `htmx.ajax()`, rather than a declarative `hx-trigger` — a runtime-reconfigurable poll interval via `hx-trigger` was found unreliable in real-browser testing. The layout editor (`static/js/layout_editor.js`) implements drag/resize with raw pointer events, no drag library.

**Navigation**: sidebar (`templates/base.html`) has three top-level entries — Dashboard, レイアウト編集 (layout editor), システム設定 (settings hub). The settings hub links out to Online設定 (`/ui/api-sources`), タグマッピング (`/ui/tag-mappings`), and Offline設定 (`/ui/standalone`) — these are sub-pages of settings, not separate nav items, tracked via each nav item's `also: [...]` list for active-state highlighting (implemented with a Jinja `namespace()` since `{% set %}` doesn't persist across `{% for %}` iterations).

CSS (`static/css/main.css`) defines both themes via `@media (prefers-color-scheme: dark)` and `:root[data-theme="dark"/"light"]` overrides (manual toggle wins over OS preference), plus a separate `--diagram-*` token set for the equipment canvas — the canvas is always a fixed white "paper" background regardless of app theme, so its colors are not part of the light/dark token system.
