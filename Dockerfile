# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster
LABEL description="Python FastAPI: Bank Ledger WebApp" 

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="${PYTHONPATH}:/app" \

RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get clean \
    && pip install --upgrade pip \
    && pip install uvicorn fastapi environs redbox

COPY . /app
EXPOSE 80

CMD ["python3", "app/run.py"]
