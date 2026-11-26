FROM python:3.14.9-slim-bookworm@sha256:945c2676dc2b18e0c1f16879244122c57c0ffede60006bf3df159c507a31bcae

ARG TARGETARCH
ARG HERMES_AGENT_COMMIT=8fc0374447313e276f6b9a2764bfc750190c966a
ARG HERMES_AGENT_SHA256=875e633ae5b3c6349c1bcffc18c0476518fbe5dead355e4aa09ad827ebffce0c
ARG HERMES_WEBUI_COMMIT=ff60081cadd9587a6e7e48a1e9daf898b502a88a
ARG HERMES_WEBUI_SHA256=3d7961176b6296f5b91e453a7d5bb1d380cbfe9af6c33d448390a2c021c2a5a6
ARG UV_VERSION=0.13.5

ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    VIRTUAL_ENV=/opt/hermes-venv \
    PATH=/opt/hermes-venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    HERMES_HOME=/data/.hermes \
    HERMES_AGENT_DIR=/opt/hermes-agent \
    HERMES_WEBUI_DIR=/opt/hermes-webui \
    HERMES_WEBUI_HOST=0.0.0.0 \
    HERMES_WEBUI_PORT=8787 \
    HERMES_WEBUI_STATE_DIR=/data/.hermes/webui \
    HERMES_WEBUI_AGENT_DIR=/opt/hermes-agent \
    HERMES_WEBUI_DEFAULT_WORKSPACE=/workspace \
    HERMES_DISABLE_LAZY_INSTALLS=1 \
    HERMES_WEBUI_AUTO_INSTALL=0

WORKDIR /workspace

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        bash ca-certificates curl git tini tzdata \
    && update-ca-certificates \
    && ln -snf /usr/share/zoneinfo/"$TZ" /etc/localtime \
    && echo "$TZ" > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

RUN set -eu; \
    case "$TARGETARCH" in \
      amd64) uv_target=x86_64-unknown-linux-gnu; uv_sha=f68d291c75783122dad58ab77def0e13f3233f358731db5d6d7e8715603b928f ;; \
      arm64) uv_target=aarch64-unknown-linux-gnu; uv_sha=4bb69cf95ed13f23713bb7bc09f241896ea0c75b7c557e615a20604b82f9c403 ;; \
      *) echo "unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac; \
    curl -fL --retry 5 -o /tmp/uv.tar.gz "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-${uv_target}.tar.gz"; \
    echo "$uv_sha  /tmp/uv.tar.gz" | sha256sum -c -; \
    tar -xzf /tmp/uv.tar.gz -C /tmp; \
    install -m 0755 "/tmp/uv-${uv_target}/uv" /usr/local/bin/uv; \
    rm -rf /tmp/uv.tar.gz "/tmp/uv-${uv_target}"

RUN set -eu; \
    curl -fL --retry 5 -o /tmp/agent.tar.gz "https://github.com/NousResearch/hermes-agent/archive/${HERMES_AGENT_COMMIT}.tar.gz"; \
    echo "$HERMES_AGENT_SHA256  /tmp/agent.tar.gz" | sha256sum -c -; \
    mkdir -p "$HERMES_AGENT_DIR"; \
    tar -xzf /tmp/agent.tar.gz -C "$HERMES_AGENT_DIR" --strip-components=1; \
    curl -fL --retry 5 -o /tmp/webui.tar.gz "https://github.com/nesquena/hermes-webui/archive/${HERMES_WEBUI_COMMIT}.tar.gz"; \
    echo "$HERMES_WEBUI_SHA256  /tmp/webui.tar.gz" | sha256sum -c -; \
    mkdir -p "$HERMES_WEBUI_DIR"; \
    tar -xzf /tmp/webui.tar.gz -C "$HERMES_WEBUI_DIR" --strip-components=1; \
    rm -f /tmp/agent.tar.gz /tmp/webui.tar.gz

RUN set -eu; \
    uv venv --python /usr/local/bin/python "$VIRTUAL_ENV"; \
    UV_PROJECT_ENVIRONMENT="$VIRTUAL_ENV" uv sync --frozen --all-packages --no-dev \
      --python "$VIRTUAL_ENV/bin/python" --project "$HERMES_AGENT_DIR"; \
    case "$TARGETARCH" in \
      amd64) \
        yaml_name=pyyaml-6.0.4-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl; \
        yaml_url=https://files.pythonhosted.org/packages/ef/1b/54ce11b40c8fa1883f14eef46525c3c329509dcc268164074fbe60add8ed/pyyaml-6.0.4-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl; \
        yaml_sha=c604dc2613c417130479cdd6e55c2faa691b6365aa82b3dafddfcecc2eaf1ac7 ;; \
      arm64) \
        yaml_name=pyyaml-6.0.4-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl; \
        yaml_url=https://files.pythonhosted.org/packages/7f/a1/88baf9d84981ea723fc1dd5cb534548caebff3071939f899509ab7c62d2f/pyyaml-6.0.4-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl; \
        yaml_sha=ed9b957abb12f6ffcd92d5db32fa3ffd4e4a8423d80ddd51b4efa63b42f6a76b ;; \
    esac; \
    curl -fL --retry 5 -o "/tmp/$yaml_name" "$yaml_url"; \
    echo "$yaml_sha  /tmp/$yaml_name" | sha256sum -c -; \
    uv pip install --python "$VIRTUAL_ENV/bin/python" --no-deps "/tmp/$yaml_name"; \
    rm -f "/tmp/$yaml_name"; \
    "$VIRTUAL_ENV/bin/python" -c 'import hermes_cli,openai,httpx,yaml,cryptography'; \
    hermes --version

COPY entrypoint.sh /usr/local/bin/hermes-entrypoint
RUN chmod 0755 /usr/local/bin/hermes-entrypoint \
    && mkdir -p "$HERMES_HOME" "$HERMES_WEBUI_STATE_DIR" /workspace

EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${HERMES_WEBUI_PORT}/health" || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/hermes-entrypoint"]
