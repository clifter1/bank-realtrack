# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster
LABEL description="Python FastAPI: Bank Ledger WebApp" 

ENV USERNAME= \
    PASSWORD= \
    IMAPPATH= \
    LOGLEVEL=info \
    IMAPPORT=993 \
    DATABASE=data.db

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH="${PYTHONPATH}:/app" \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.4.2

RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get clean \
    && pip install --upgrade pip \
    && pip install "poetry==$POETRY_VERSION"

WORKDIR /app

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-ansi --no-interaction
COPY run.py ./

EXPOSE 80
CMD ["poetry", "run", "python", "run.py"]
