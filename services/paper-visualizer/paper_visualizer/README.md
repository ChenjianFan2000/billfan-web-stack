# Paper Visualizer

A local web application that catalogs and teaches the MATHPROVER project's
papers at theorem-level depth (30–60 min per paper), bilingual (Chinese /
English), with an AI Q&A sidebar streaming via VectorEngine.

## Architecture

- **Backend**: Python 3.11 + FastAPI. Two one-shot scripts (`ingest.py`,
  `generate.py`) produce git-tracked content under `backend/content/`.
  `api.py` serves JSON + SSE streaming chat.
- **Frontend**: Vue 3 + Vite + TypeScript + Pinia + Tailwind CSS. Parses
  teaching Markdown client-side with markdown-it + KaTeX + custom
  `:::theorem` / `:::proof-sketch` containers.

## Setup (one-time)

```bash
# Backend deps
pip install -r paper_visualizer/requirements.txt

# Frontend deps
cd paper_visualizer/frontend && npm install && cd -

# Secrets
cp paper_visualizer/.env.example paper_visualizer/.env
# Edit paper_visualizer/.env and paste a working VectorEngine API key
# Default model is claude-sonnet-4-6 (changeable via PAPER_VISUALIZER_MODEL).
```

## Build the content (once, and whenever papers change)

```bash
# Pull env vars into the shell
export $(grep -v '^#' paper_visualizer/.env | xargs)

# Parse LaTeX → structured meta.json (idempotent, hash-cached)
python -m paper_visualizer.backend.ingest

# AI-generate bilingual teaching Markdown (idempotent by prompt version)
python -m paper_visualizer.backend.generate
```

`ingest` takes seconds. `generate` takes ~1–2 minutes per paper per language.
For 8 papers × 2 languages, budget ~30 minutes.

Flags:
- `--slug SLUG` — run for a single paper.
- `--force` — ignore caches, regenerate.
- `--lang {zh,en,both}` — limit to one language.

## Run (dev)

```bash
bash paper_visualizer/scripts/run_dev.sh
# Open http://localhost:5173
```

Backend runs on `:8000`, frontend on `:5173` with `/api` proxy.

## Run (prod, single process)

```bash
bash paper_visualizer/scripts/build_prod.sh
# Open http://localhost:8000
```

## Add a new paper

1. Place it at `output/project9/main.tex` (or `main_v2.tex`).
2. Re-run:
   ```bash
   python -m paper_visualizer.backend.ingest
   python -m paper_visualizer.backend.generate
   ```
3. Reload the frontend — the new paper appears on the home grid.

## Tests

```bash
# Backend
python -m pytest paper_visualizer/tests/ -v

# Frontend
cd paper_visualizer/frontend && npm run test
```

## Manual QA checklist

- [ ] Home shows all papers, filter sidebar checkboxes work
- [ ] Search box narrows the grid
- [ ] Click a card → detail loads, math renders, ToC scrolls, theorem cards styled
- [ ] Language toggle swaps content between zh and en
- [ ] Proof sketches collapse/expand
- [ ] "Ask Claude" opens chat panel, messages stream, survive reload (localStorage)
- [ ] Add a new paper to `output/`, rerun ingest+generate, refresh, new card appears

## Directory layout

```
paper_visualizer/
├── backend/
│   ├── ingest.py            # LaTeX → meta.json
│   ├── generate.py          # AI → zh.md + en.md + classification
│   ├── api.py               # FastAPI endpoints
│   ├── latex_parse.py       # pylatexenc-based extraction
│   ├── prompts.py           # TEACH / CLASSIFY / CHAT templates
│   ├── schemas.py           # Pydantic models
│   ├── vector_client.py     # openai SDK → VectorEngine wrapper
│   └── content/             # generated per-paper content (git-tracked)
├── frontend/
│   ├── src/
│   │   ├── views/           # HomeView, PaperDetailView, TagIndexView, AboutView
│   │   ├── components/      # PaperCard, TheoremCard, ChatPanel, ...
│   │   ├── stores/          # Pinia stores (papers, chat, lang)
│   │   ├── composables/     # useChat (SSE streaming)
│   │   ├── api.ts           # typed fetch wrappers
│   │   ├── i18n.ts          # zh/en strings
│   │   └── router.ts        # Vue Router routes
│   ├── package.json
│   └── vite.config.ts
├── scripts/
│   ├── run_dev.sh
│   └── build_prod.sh
├── tests/                   # pytest backend tests
├── requirements.txt
├── .env.example
└── README.md
```

## Notes

- VectorEngine base URL must end in `/v1` (OpenAI-compatible path).
- Backend `vector_client.chat()` internally uses streaming and concatenates
  tokens, because large non-streaming responses from the upstream gateway
  can drop with SSL record-MAC errors.
- `backend/content/` is git-tracked intentionally: you can edit the generated
  Markdown by hand to polish specific papers without rerunning the AI.
