FROM python:3.13-alpine

WORKDIR /usr/src/norminette

COPY pyproject.toml poetry.lock README.md ./
COPY norminette/ ./norminette/

RUN pip3 install --no-cache-dir 'poetry>=2,<3' --root-user-action=ignore \
    && poetry build \
    && pip3 install dist/*.whl --root-user-action=ignore

WORKDIR /code

ENTRYPOINT ["norminette"]
