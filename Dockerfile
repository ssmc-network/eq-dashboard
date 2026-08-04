# ==========================================
# グローバル設定
# ==========================================
ARG PYTHON_VERSION=ubi9/python-312-minimal
ARG POETRY_VERSION=2.1.2


# ==========================================
# ベースイメージ
# ==========================================
FROM registry.access.redhat.com/${PYTHON_VERSION}:latest AS base
ARG HTTP_PROXY, HTTPS_PROXY
WORKDIR /opt/app-root/src/project/app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_INSTALLER_MAX_WORKERS=10 \
    POETRY_VIRTUALENVS_CREATE=false \
    VIRTUAL_ENV=/opt/app-root

USER 0


# ==========================================
# 依存関係のビルド(poetry, pipパッケージ)
# ==========================================
FROM base AS dependencies
ARG HTTP_PROXY, HTTPS_PROXY
ARG POETRY_VERSION

USER 1001
RUN pip install --upgrade --no-cache-dir pip && \
    pip install --no-cache-dir poetry=="${POETRY_VERSION}"

COPY --chown=1001:0 ./app/pyproject.toml ./app/poetry.lock /opt/app-root/src/project/app/

RUN poetry install --without dev --no-root && \
    poetry cache clear pypi --all


# ==========================================
# 開発用イメージ (dev)
# ==========================================
FROM dependencies AS dev
ARG HTTP_PROXY, HTTPS_PROXY

USER 0
RUN --mount=type=cache,target=/var/cache/dnf \
    microdnf install -y --setopt=tsflags=nodocs \
    git tar

USER 1001
# キャッシュを効かせるためにpyproject.tomlだけ先にコピー
COPY --chown=1001:0 ./app/pyproject.toml ./app/poetry.lock /opt/app-root/src/project/app/
RUN poetry install --no-root && \
    poetry cache clear pypi --all

COPY --chown=1001:0 . /opt/app-root/src/project


# ==========================================
# 本番用イメージ (prd)
# ==========================================
FROM dependencies AS prd

COPY --chown=1001:0 ./app /opt/app-root/src/project/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "log_config.yaml"]
EXPOSE 8000
