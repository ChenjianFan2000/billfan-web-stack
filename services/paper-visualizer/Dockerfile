# ---- Stage 1: build the Vue frontend ----
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY paper_visualizer/frontend/package.json paper_visualizer/frontend/package-lock.json ./
RUN npm ci
COPY paper_visualizer/frontend/ ./
RUN npm run build

# ---- Stage 2: runtime (Python + static assets) ----
FROM python:3.11-slim AS runtime
WORKDIR /app

# System deps kept minimal (pylatexenc is pure-python; no build toolchain needed)
RUN pip install --no-cache-dir --upgrade pip

# Python deps
COPY paper_visualizer/requirements.txt ./paper_visualizer/requirements.txt
RUN pip install --no-cache-dir -r paper_visualizer/requirements.txt

# Backend code + pre-built paper content (tracked in git)
COPY paper_visualizer/backend/ ./paper_visualizer/backend/
# The "paper_visualizer" package has no __init__.py at its root; create an
# empty one so Python treats the directory as a regular package.
RUN touch paper_visualizer/__init__.py

# Built frontend → served by FastAPI as static files
COPY --from=frontend-build /app/frontend/dist ./paper_visualizer/frontend/dist

ENV PYTHONUNBUFFERED=1
ENV PAPER_VISUALIZER_HOST=0.0.0.0
ENV PAPER_VISUALIZER_PORT=8000

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "paper_visualizer.backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
