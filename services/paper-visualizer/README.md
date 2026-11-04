# Paper Visualizer

A self-contained web application for browsing and *teaching* a collection of
computational-finance research papers. Ships with **11 papers** pre-indexed
at theorem-level depth, bilingual (中文 / English) teaching material, and an
AI Q&A sidebar that streams answers about each paper.

**Built out of the MATHPROVER v2.0 pipeline** (see
[mathprover-platform](https://github.com/BillFan)). All quality metrics —
Critic verdict, Significance score, Tier (A/B/C), per-dimension ratings — are
extracted from the original pipeline evaluations and shown in the sidebar.

---

## TL;DR — deploy in one command

```bash
git clone https://github.com/<owner>/paper-visualizer.git
cd paper-visualizer

# Provide an OpenAI-compatible API key (VectorEngine is the default)
cp paper_visualizer/.env.example paper_visualizer/.env
$EDITOR paper_visualizer/.env   # fill in VECTORENGINE_API_KEY=sk-...

docker compose up -d --build
# Open http://localhost:8000
```

The image serves both the FastAPI backend and the pre-built Vue frontend on
port 8000. No ingestion step is needed at deploy time: all paper data
(teaching Markdown, meta.json, source .tex, source .pdf) is committed in
`paper_visualizer/backend/content/`.

---

## What you get (after `docker compose up`)

- `GET /` — the frontend (Vue 3 + Tailwind + KaTeX)
- `GET /api/health` — `{status, papers_count}`
- `GET /api/papers` — index card data for all papers
- `GET /api/papers/{slug}` — full meta + bilingual teaching content
- `GET /api/tags` — filter facets
- `GET /content/{slug}/source.pdf` — original compiled paper
- `GET /content/{slug}/source.tex` — original LaTeX source
- `POST /api/chat` (SSE stream) — ask-the-paper chat, returns `event: token` frames

---

## What's bundled

```
paper_visualizer/backend/content/
├── papers.json            # home-grid index
├── tags.json              # filter facets
├── cross_impact/          # one of 11 paper directories
│   ├── meta.json          # structured bilingual metadata + quality scores
│   ├── zh.md              # ~500-line Chinese teaching doc
│   ├── en.md              # ~500-line English teaching doc
│   ├── source.tex         # original LaTeX — chat reads from here
│   ├── source.pdf         # original compiled paper — served at /content/.../source.pdf
│   └── .source_hash       # idempotent ingest cache marker
├── discrete_vs_rough/
├── mv_games/
├── project7/
├── project8/
├── sr_p001/  sr_p005/  sr_p006/   # structural_research provenance
├── uniswap_tick_correction/
├── var_ratio/
└── variance_options/
```

The 8 `output/*` papers come from the Realresearch repo; the 3 `sr_*` papers
come from `structural_research`. The visualizer unifies both.

---

## Configuration (`paper_visualizer/.env`)

| Variable | Default | Purpose |
|---|---|---|
| `VECTORENGINE_API_BASE` | `https://api.vectorengine.ai/v1` | OpenAI-compatible base URL |
| `VECTORENGINE_API_KEY` | (required) | Your API key |
| `PAPER_VISUALIZER_MODEL` | `claude-sonnet-4-6` | Model for content generation (dev only) |
| `PAPER_VISUALIZER_CHAT_MODEL` | `claude-sonnet-4-6` | Model that powers the in-app chat |
| `PAPER_VISUALIZER_SOURCE_ROOT` | parent of `paper_visualizer/` | Where `ingest` looks for `output/{slug}/main*.tex` (dev only) |
| `PAPER_VISUALIZER_STRUCTURAL_ROOT` | (unset) | Optional second repo to scan (dev only) |

Any endpoint that speaks the OpenAI chat-completions API works — swap
`VECTORENGINE_API_BASE` to point at Anthropic, OpenAI, DeepSeek, etc.

---

## Native deployment (without Docker)

```bash
# Backend
python -m pip install -r paper_visualizer/requirements.txt

# Frontend (build once)
cd paper_visualizer/frontend
npm ci
npm run build
cd -

# Pull env vars into the shell
export $(grep -v '^#' paper_visualizer/.env | xargs)

# Run
python -m uvicorn paper_visualizer.backend.api:app --host 0.0.0.0 --port 8000
```

---

## Development

```bash
# one-shot: backend on :8000, Vite dev on :5173 (proxies /api and /content)
bash paper_visualizer/scripts/run_dev.sh
```

**Add a new paper** (requires access to the original Realresearch or
structural_research checkout):

```bash
export PAPER_VISUALIZER_SOURCE_ROOT=/path/to/Realresearch
export PAPER_VISUALIZER_STRUCTURAL_ROOT=/path/to/structural_research  # optional

# Parse LaTeX → structured meta.json (idempotent, hash-cached)
python -m paper_visualizer.backend.ingest

# AI-generate bilingual teaching Markdown (idempotent by prompt version)
python -m paper_visualizer.backend.generate

# (Optional) run unified AI quality assessment on any paper missing scores
python -m paper_visualizer.backend.assess_quality
```

Flags: `--slug SLUG`, `--force`, `--lang {zh,en,both}`.

---

## Architecture

- **Backend** — Python 3.11 + FastAPI + Pydantic. Three one-shot scripts
  (`ingest.py`, `generate.py`, `assess_quality.py`) produce git-tracked
  content under `backend/content/`. `api.py` serves JSON + SSE chat.
- **Frontend** — Vue 3 + Vite + TypeScript + Pinia + Tailwind. Renders
  teaching Markdown client-side with markdown-it + KaTeX, plus custom
  `:::theorem{...}` / `:::proof-sketch{...}` containers and LaTeX
  cross-reference cleanup (`\Cref`, `\ref`, `\eqref`, `\cite`, `\emph`,
  `\textbf`, `\textit`, ...).
- **Chat** — SSE streaming via `fetch` + `ReadableStream`; system prompt
  embeds the paper's abstract, theorem statements, and truncated source.tex.

```
paper-visualizer/
├── Dockerfile
├── docker-compose.yml
├── README.md (this file)
├── LICENSE
└── paper_visualizer/
    ├── .env.example
    ├── README.md                # original (developer-oriented) notes
    ├── requirements.txt
    ├── backend/
    │   ├── api.py               # FastAPI app
    │   ├── ingest.py            # LaTeX → meta.json (dev only)
    │   ├── generate.py          # AI → zh.md + en.md (dev only)
    │   ├── assess_quality.py    # unified AI Critic (dev only)
    │   ├── eval_extract.py      # pipeline-quality extraction
    │   ├── latex_parse.py       # pylatexenc-based extraction
    │   ├── prompts.py
    │   ├── schemas.py
    │   ├── vector_client.py     # OpenAI SDK → VectorEngine wrapper
    │   └── content/             # 11 paper dirs (git-tracked) + index JSONs
    ├── frontend/
    │   ├── src/                 # Vue components, views, stores, i18n, router
    │   ├── index.html
    │   ├── package.json
    │   └── vite.config.ts
    ├── scripts/
    │   ├── run_dev.sh
    │   └── build_prod.sh
    └── tests/                   # pytest backend tests
```

---

## Notes for deploying agents

1. **Do NOT rerun ingest/generate on first deploy.** The content dir is
   authoritative and committed. Running `generate` would overwrite it with
   whatever the current model produces and requires access to the original
   LaTeX trees that are NOT shipped with this repo.
2. `VectorEngine` base URL **must end in `/v1`** (OpenAI-compatible path).
3. The chat endpoint uses streaming internally (`vector_client.chat_stream`);
   large non-streaming responses from some gateways drop with SSL
   record-MAC errors, so we avoid them.
4. Ports: backend listens on 8000; dev frontend on 5173. Docker exposes 8000.
5. All bundled PDFs and .tex files live under `backend/content/{slug}/`.
   They are served verbatim at `/content/{slug}/source.{pdf,tex}`.

---

## Manual smoke test

- [ ] Home page lists all 11 papers with Tier + Significance badges
- [ ] Filter sidebar: toggling "Repo" / "Domain" / "Math tools" narrows the grid
- [ ] Search box narrows the grid
- [ ] Clicking a card → detail loads, math renders, ToC scrolls
- [ ] Language toggle swaps entire page between zh ↔ en
- [ ] Proof sketches collapse/expand
- [ ] "Ask Claude" opens chat panel; messages stream; survive reload
- [ ] "Open PDF" / "Open Tex" buttons serve the original source

## License

MIT. See [LICENSE](LICENSE).
