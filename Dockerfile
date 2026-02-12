# EvoCodeBenchPlus - code generation benchmark (MVP: repos baked in)
FROM --platform=linux/amd64 python:3.11-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# System deps (build-essential, x11/xorg for headless testing if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    wget \
    build-essential \
    libx11-dev \
    xorg-dev \
    libglu1-mesa-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first so this layer caches when only app code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Dataset: task list + download and extract repos (large layer)
COPY bash/ bash/
COPY dataset/data/oracle.jsonl dataset/data/oracle.jsonl
RUN bash bash/load_data.sh

# App code and per-repo venvs
RUN mkdir -p venvs
COPY setup_venvs.py utils.py run_tests.py exceptions.py ./
COPY evaluate/ evaluate/
COPY setup-venvs/ setup-venvs/
RUN python setup_venvs.py

CMD ["/bin/bash"]
