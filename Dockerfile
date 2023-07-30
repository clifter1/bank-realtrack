# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster
LABEL description="Python FastAPI: Bank Ledger WebApp" 

ENV USERNAME= \
    PASSWORD= \
    IMAPPATH= \
    WEBSPORT=80 \
    LOGLEVEL=info \
    IMAPPORT=993 \
    DATADIRS=/data \
    DATABASE=data.db \
    TIMEZONE=America/New_York

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
    && apt-get -y install curl cron \
    && apt-get clean \
    && pip install --upgrade pip \
    && pip install "poetry==${POETRY_VERSION}" \
    && ln -fs /usr/share/zoneinfo/${TIMEZONE} /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && touch /etc/cron.d/sync-cron \
    && echo "1 0 1 * * curl http://localhost:${WEBSPORT}/total" >> /etc/cron.d/sync-cron \
    && echo "5 0 1 * * curl http://localhost:${WEBSPORT}/reset" >> /etc/cron.d/sync-cron \
    && chmod 0644 /etc/cron.d/sync-cron \
    && crontab /etc/cron.d/sync-cron \
    && mkdir ${DATADIRS}

WORKDIR /app

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-ansi --no-interaction
COPY run.py ./

EXPOSE ${WEBSPORT}
HEALTHCHECK --timeout=5s --start-period=10s CMD curl --fail http://localhost:${WEBSPORT}/health || exit 1
CMD ["sh", "-c", "cron && poetry run python run.py"]
