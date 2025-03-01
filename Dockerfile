FROM python:3.12-slim

WORKDIR /usr/src/norminette

COPY pyproject.toml poetry.lock README.md ./
COPY norminette ./norminette

RUN pip3 install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --without dev

WORKDIR /code

ENTRYPOINT ["norminette"]
