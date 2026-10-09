FROM ghcr.io/astral-sh/uv:python3.14-alpine

WORKDIR /usr/src/norminette

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY norminette/ ./norminette/

RUN apk add --no-cache gettext \
    && for po in norminette/locale/*/LC_MESSAGES/norminette.po; do \
           msgfmt "$po" -o "${po%.po}.mo"; \
       done \
    && uv build --no-cache \
    && uv pip install --system --no-cache dist/*.whl

WORKDIR /code

ENTRYPOINT ["norminette"]
