# syntax=docker/dockerfile:1.7

# uv is pinned by copying the binary out of its own versioned image. The
# combined <uv-version>-python<ver>-<distro> tags stopped at 0.4.x, so
# ghcr.io/astral-sh/uv:0.11.21-python3.12-bookworm-slim does not exist; the
# only current combined tag (python3.12-bookworm-slim) floats on uv version,
# which would break the pin-your-versions rule.
FROM python:3.12-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /uvx /bin/

WORKDIR /build
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev 2>/dev/null \
    || uv sync --no-install-project --no-dev

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-dev

# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runner

RUN groupadd -r -g 1001 toa && useradd -r -u 1001 -g toa -m -d /home/toa toa

COPY --from=builder --chown=toa:toa /build/.venv /app/.venv
COPY --from=builder --chown=toa:toa /build/src /app/src

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TOA_RULES_PATH=/srv/toa-rules \
    TOA_MCP_HOST=0.0.0.0 \
    TOA_MCP_PORT=8000

WORKDIR /app
USER toa
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz',timeout=4).status==200 else 1)"

CMD ["python", "-m", "toa_mcp.server"]
