# EvoCodeBenchPlus - code generation benchmark (MVP: repos baked in)
FROM --platform=linux/amd64 python:3.11-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends sudo wget build-essential libx11-dev xorg-dev libglu1-mesa-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN mkdir -p dataset/data
COPY dataset/data/oracle.jsonl dataset/data/oracle.jsonl
COPY ./bash ./bash

RUN bash bash/load_data.sh

COPY setup_venvs.py .
COPY utils.py .
RUN pip install tqdm pytest numpy tiktoken psutil func_timeout

RUN mkdir venvs
COPY setup-venvs ./setup-venvs
RUN python setup_venvs.py

CMD ["/bin/bash"]
