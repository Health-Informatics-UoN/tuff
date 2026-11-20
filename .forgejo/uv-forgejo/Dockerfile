# nonsense dockerfile
FROM ghcr.io/astral-sh/uv:debian-slim

RUN apt update \
   && apt -q install -y --no-install-recommends \
       nodejs \
       npm \
   && apt -q remove -y python python3 \
   && apt -q clean \
   && rm -rf /var/lib/apt/lists/*
