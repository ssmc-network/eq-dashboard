# ==========================================
# グローバル設定
# ==========================================
ARG PYTHON_VERSION=ubi10/python-314-minimal:1785806428
ARG POETRY_VERSION=2.4.1


# ==========================================
# ベースイメージ
# ==========================================
FROM registry.access.redhat.com/${PYTHON_VERSION} AS base
ARG HTTP_PROXY, HTTPS_PROXY
WORKDIR /opt/app-root/src/project/app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_INSTALLER_MAX_WORKERS=10 \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true

USER 0


# ==========================================
# 依存関係のビルド(poetry, pipパッケージ)
# ==========================================
# poetry自体はここ(dependencies/dev-dependencies)のシステムPython側に入るだけ。
# dev/prdへ引き継ぐのは`poetry install`が作る.venv(プロジェクト内仮想環境)のみ
# (下のdev/prdステージのCOPY --fromを参照)。poetry自身やそのビルド時限りの
# 依存(setuptools、dulwichなど)が本番イメージに紛れ込むのを防ぐための構成。
# VIRTUAL_ENV/PATHはこのステージではまだ設定しない — .venvが存在する前に
# VIRTUAL_ENVを見せるとpoetryの仮想環境検出と衝突する可能性があるため、
# 実際に.venvをCOPYし終えたdev/prdステージ側でのみ設定する。
FROM base AS dependencies
ARG HTTP_PROXY, HTTPS_PROXY
ARG POETRY_VERSION

USER 1001
RUN pip install --upgrade --no-cache-dir pip && \
    pip install --no-cache-dir poetry=="${POETRY_VERSION}" && \
    poetry config virtualenvs.options.no-pip true

COPY --chown=1001:0 ./app/pyproject.toml ./app/poetry.lock /opt/app-root/src/project/app/

RUN poetry install --without dev --no-root && \
    poetry cache clear pypi --all


# ==========================================
# 依存関係のビルド(devグループを含む完全版)
# ==========================================
FROM dependencies AS dev-dependencies
ARG HTTP_PROXY, HTTPS_PROXY

RUN poetry install --no-root && \
    poetry cache clear pypi --all


# ==========================================
# 開発用イメージ (dev)
# ==========================================
FROM base AS dev
ARG HTTP_PROXY, HTTPS_PROXY
ENV VIRTUAL_ENV=/opt/app-root/src/project/app/.venv \
    PATH=/opt/app-root/src/project/app/.venv/bin:$PATH

USER 0
RUN --mount=type=cache,target=/var/cache/dnf \
    microdnf install -y --setopt=tsflags=nodocs \
    git tar

USER 1001
COPY --from=dev-dependencies --chown=1001:0 /opt/app-root/src/project/app/.venv /opt/app-root/src/project/app/.venv
COPY --chown=1001:0 . /opt/app-root/src/project
RUN chmod -R g+rwX /opt/app-root/src/project/app/data


# ==========================================
# 本番用イメージ (prd)
# ==========================================
FROM base AS prd
ENV VIRTUAL_ENV=/opt/app-root/src/project/app/.venv \
    PATH=/opt/app-root/src/project/app/.venv/bin:$PATH

USER 1001
COPY --from=dependencies --chown=1001:0 /opt/app-root/src/project/app/.venv /opt/app-root/src/project/app/.venv
COPY --chown=1001:0 ./app /opt/app-root/src/project/app
RUN chmod -R g+rwX /opt/app-root/src/project/app/data

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "log_config.yaml"]
EXPOSE 8000
