# container with npm/npx and uv
FROM ghcr.io/astral-sh/uv:debian-slim

RUN apt update \
    && apt -q install -y --no-install-recommends \
        nodejs \
        npm \
    && npm i -g npx \
    && apt -q clean \
    && rm -rf /var/lib/apt/lists/*

RUN npm -v && npx -v && uv --version && node -v
