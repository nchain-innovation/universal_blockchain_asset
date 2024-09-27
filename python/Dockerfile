FROM python:3.12-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/London
ENV DEBIAN_FRONTEND="noninteractive"

RUN apt-get update && apt-get install -y \
    build-essential  \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt \
    && rm requirements.txt

FROM base AS release
RUN apt-get update && apt-get install -y \
    curl  \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/python
COPY ./src /app/python

# env var to detect we are in a docker instance
ENV APP_ENV=docker
CMD ["bash"]