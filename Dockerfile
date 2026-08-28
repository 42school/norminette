FROM ghcr.io/astral-sh/uv:python3.14-alpine

WORKDIR /usr/src/norminette

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY norminette/ ./norminette/

RUN uv build --no-cache \
    && uv pip install --system --no-cache dist/*.whl

WORKDIR /code

ENTRYPOINT ["norminette"]
