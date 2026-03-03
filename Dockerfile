FROM python:3.13-slim-bookworm AS python-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONOPTIMIZE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    APP_PATH="/app"

ENV VIRTUAL_ENV="$APP_PATH/.venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR $APP_PATH

FROM python-base AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/

RUN pip install --no-cache-dir uv

COPY ./pyproject.toml ./uv.lock ./
RUN uv venv -p 3.13 \
    && uv sync --all-extras --no-install-project
COPY ./src/highload_payments ./highload_payments
RUN uv sync --all-extras --no-editable

FROM builder AS runner

COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
