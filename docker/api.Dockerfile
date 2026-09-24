# API image (technical spec §10.4). Build context = repo root.
FROM node:22-bookworm-slim AS web
RUN npm install -g pnpm@10.34.5
WORKDIR /repo
COPY . .
RUN pnpm install --frozen-lockfile && pnpm build:web
FROM python:3.12-slim-bookworm
RUN pip install --no-cache-dir uv==0.12.18
WORKDIR /app
COPY server/pyproject.toml server/uv.lock ./
RUN uv sync --frozen --no-dev
COPY server/ ./
COPY packages/content /content
COPY --from=web /repo/apps/console/dist /app/static/console
COPY --from=web /repo/apps/operator/dist-web /app/static/app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
