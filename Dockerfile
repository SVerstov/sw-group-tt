FROM ghcr.io/astral-sh/uv:python3.13-alpine

ADD . /app

WORKDIR /app
RUN uv sync --locked

RUN mv .env.prod .env

RUN uv run manage.py collectstatic  --noinput


