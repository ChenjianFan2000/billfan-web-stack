# Repository Guidelines

This checkout is the **live deployment root** (`/var/www`) for several sites on this host.
It is **not a git repo** — there is no `.git`, so no history, branches, or rollback via git.
Always copy a file before large edits, and keep deploys reversible.

## Deployed sites (verified against `/etc/nginx/conf.d`)

| Host | Status | Serving mechanism |
|---|---|---|
| `billfan.cn` / `www.billfan.cn` | **active** (HTTP+HTTPS, `www` 301 → apex) | static build `/var/www/dist` + `/api/` proxied to `127.0.0.1:8000` (systemd `qh-paper-assistant`). Certs from `/etc/letsencrypt/live/billfan.cn/` |
| `aimath.billfan.cn` | **retired / shut down** | dedicated vhost returns `403` + `X-Robots-Tag: noindex`, `robots.txt` disallows all. On `billfan.cn`, `/aimath`, `/aimath/*`, `/api/aimath`, `/api/aimath/*` are also `403` |
| `tongnian.billfan.cn` | **active** (HTTP 301 → HTTPS) | static site `/var/www/tongnian` + `/api/` proxied to `127.0.0.1:8010` (systemd `line-sync`, `services/line_sync/`) | (the `line-story` subdir of `ChenjianFan2000/childhood-reading-classroom`): `index.html` 授课台, `subtitles.html` 字幕台, `presenter.html` 教师台. Certs from `/etc/letsencrypt/live/tongnian.billfan.cn/`. `/line-story/` 前缀 alias 到同一目录（README 中手机读稿用该路径） |
| `ark.billfan.cn` | **not currently hosted here** | no nginx vhost, no listening process. Source lives in `services/paper-visualizer/` but nothing serves it today |

> `docker` is **not installed** on this host. Anything documented with `docker compose` (e.g. `paper-visualizer`) must be run natively from its own venv instead.

## Project Structure & Module Organization

- `app/` — FastAPI backend (the active app). `main.py:52` builds the app and mounts every router; it also installs a host-dispatch middleware (`main.py:63`) that rewrites `/api/{health,papers,tags,chat,...}` → `/api/aimath/...` when `Host == aimath.billfan.cn`. That path is unreachable in production now (nginx 403s first) — treat `app/aimath.py` as legacy unless aimath is explicitly revived.
  - `papers.py`: `/api/papers*` CRUD, file download, quarantine list, `/api/stats`
  - `upload.py`: PDF intake (nginx allows 120m), then `pipeline.py` (2.2k lines) does extraction, dedup by char-ngram Jaccard, Qwen cleaning/quality guardrails, quarantine decisions
  - `pipeline.py` + `dashscope_client.py` are the LLM boundary; `db.py` owns the sqlite schema, migrations, and the `get_db` dependency
  - `agent.py` (2.2k lines) chat agent/tool calling, `export.py` exports, `categories.py` / `paper_categories.py` taxonomy, `auth.py` JWT, `settings*.py` persisted settings, `logger.py`
- `frontend/` — React 19 + Vite 7 + TS (strict) + Tailwind 3 + KaTeX via `react-markdown`. Output must be copied to `/var/www/dist` — that is nginx's `root`, not `frontend/dist`.
- `services/paper-visualizer/` — standalone FastAPI + Vue 3 app (11 pre-indexed computational-finance papers; committed teaching content in `paper_visualizer/backend/content/`; SSE chat). Own `.venv`. `app/aimath.py` reads its content through the symlink `/var/www/dist/content`. Its README warns: **do not rerun `ingest`/`generate`** — the content dir is authoritative and the source LaTeX trees aren't shipped.
- `services/line_sync/` — tiny FastAPI relay for the 《童年》 static site (`tongnian.billfan.cn`): rooms + SSE. The projected page publishes `presenterState()`; phones that scanned the QR (`subtitles.html?room=…`) follow the cue and can send transport commands back. Runs on `127.0.0.1:8010` from `/var/www/.venv` via systemd `line-sync`, proxied as `tongnian.billfan.cn/api/`. QR codes come from `segno` (installed into `.venv`). Tests: `tests/test_line_sync.py`.
- `services/paper-search-mcp/` — `uv`-managed MCP paper-search server, optional; launched by `scripts/mcp/start_paper_search_mcp.sh`.
- `deploy/` — production templates: `deploy/env/app.env.example`, `deploy/nginx/*.conf`, `deploy/systemd/qh-paper-assistant.service`. Live copies live in `/etc/qh-paper-assistant/app.env`, `/etc/nginx/conf.d/`, `/etc/systemd/system/`. Change the template *and* the live copy.
- `scripts/deploy/phase0_*.sh` — bootstrap chain (deps → runtime → push nginx/systemd → Let's Encrypt → verify); `refresh_aimath_host.sh` re-pushes the retired aimath vhost.
- `tongnian/scripts/relay.js` — 跨设备同步：非全屏按 **J** 显示房间二维码，扫码手机进入 `subtitles.html?room=…` 跟随投影画面；手机上翻页也回控投影。全屏下按 J 只提示，不投出二维码。
- `tongnian/` — static 《童年》线条叙事课件站点（上游 `line-story/`），无构建步骤，直接替换文件即可；`manifest.json` 记录各文件 sha256，可用于校验拷贝完整性。
- `scripts/build_aimath_static.py` — regenerates the static aimath site into `dist/aimath/` from the visualizer content; see `DEPLOY_AIMATH.md`.
- `data/` — live state: `db.sqlite`, `pdfs/`, `texts/`, `chat_files/`, `exports/`. `logs/` — uvicorn output. Runtime artifacts; never commit.
- `.venv/` — the Python env used by both systemd and pytest.

## Build, Test, and Development Commands

Run everything from `/var/www` (imports are absolute `app.*`, so pytest only works at the repo root).

```bash
# backend tests (no pytest.ini/pyproject — stock discovery over ./tests)
.venv/bin/python -m pytest tests -q
.venv/bin/python -m pytest tests/test_upload.py -q                 # single file
.venv/bin/python -m pytest tests/test_papers.py::test_update -q    # single test
.venv/bin/python -m pytest tests -q -k upload                      # by keyword

# backend dev server (prod runs the same command via systemd on 127.0.0.1:8000)
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# frontend
cd frontend && npm install && npm run dev        # vite :5173, proxies /api
cd frontend && npm run lint && npm run build     # build = "tsc -b && vite build"

# publish the frontend build to the directory nginx actually serves
rm -rf /var/www/dist/assets && cp -r frontend/dist/* /var/www/dist/

# service control + logs
systemctl restart qh-paper-assistant && systemctl status qh-paper-assistant
journalctl -u qh-paper-assistant -f
nginx -t && systemctl reload nginx

# optional MCP sidecar (needs uv; run scripts/mcp/setup_mcp.sh first)
./scripts/mcp/start_paper_search_mcp.sh

# aimath static regeneration (only if that host is revived)
.venv/bin/python scripts/build_aimath_static.py
```

No CI, no coverage config, and no frontend test runner.

## Coding Style & Naming Conventions

- Python: 4-space indent, `snake_case`, one module per domain under `app/`; each module exposes a module-level `router` that `main.py` mounts. Imports grouped stdlib / third-party / local. Prefer small named helpers over inline complexity — `pipeline.py` follows this heavily.
- TypeScript/React: strict TS; `PascalCase` components (`PaperManager.tsx`), `camelCase` hooks/utils, under `frontend/src/{api,components,pages,lib}`. Run `npm run lint` before proposing frontend changes.
- Comments and UI strings are largely Chinese; keep new user-facing copy Chinese to match.

## Testing Guidelines

- pytest + `fastapi.testclient.TestClient`; tests mirror backend module names (`tests/test_<feature>.py`).
- **`test_main.py` asserts app wiring, including the aimath host-rewrite behavior in `app/main.py`.** Changing routing there requires updating that test.
- Isolate DB/filesystem/env with `tmp_path` and `monkeypatch`; never point a test at `/var/www/data/db.sqlite`.
- Cover both success and failure paths for new endpoints.

## Deploy After Changing Things

1. Backend code has no effect until `systemctl restart qh-paper-assistant` (uvicorn without `--reload`).
2. Frontend changes have no effect until rebuilt and copied into `/var/www/dist`.
3. nginx/systemd/env edits: update the template under `deploy/` **and** the live file, then `nginx -t && systemctl reload nginx`.
4. `./scripts/deploy/phase0_verify.sh` is the acceptance check after environment-level work.

## Commit & Pull Request Guidelines

- No `.git` metadata here, so no local commit history is available to infer conventions.
- Use Conventional Commit style going forward (e.g., `feat(upload): validate MIME type`, `fix(auth): handle expired token`).
- PRs should include: scope summary, touched paths, test commands run, env/config changes, and UI screenshots for frontend changes.
- Call out deploy/rollback steps and which site the change affects.

## Security & Configuration Tips

- Secrets live only in `/etc/qh-paper-assistant/app.env` (sourced by the systemd unit); template is `deploy/env/app.env.example`. Never commit real keys or echo env files into output.
- Rotate `JWT_SECRET_KEY`, `DASHSCOPE_API_KEY`, `EXA_API_KEY`, and change the default `DEFAULT_USERNAME` / `DEFAULT_PASSWORD` before any production exposure.
- Outbound LLM/search traffic goes through `dashscope_client.py` and the MCP scripts; keep new external calls on those paths rather than scattering ad-hoc HTTP clients.
- `data/` holds real uploads and the live sqlite DB — don't delete or hand-edit it to "reset" state for testing.
