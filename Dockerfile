# EvoCodeBenchPlus - code generation benchmark (multi-stage: repos only in builder)
# -----------------------------------------------------------------------------
# Stage 1: build venvs and data-success using downloaded repos (repos not in final image)
# -----------------------------------------------------------------------------
FROM python:3.11-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    wget \
    build-essential \
    libx11-dev \
    xorg-dev \
    libglu1-mesa-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Dataset: task list, oracle completions; then download and extract repos
COPY bash/ bash/
COPY dataset/data/oracle.jsonl dataset/data/
COPY experiments/completions/oracle/oracle.jsonl experiments/completions/oracle/oracle.jsonl
RUN set -e && bash bash/load_data.sh && test -f dataset/data/oracle.jsonl && test -d dataset/repos && test -n "$(ls -A dataset/repos)"

# App code and venv setup (oracle gate → data-success.jsonl)
RUN mkdir -p venvs
COPY setup_venvs.py run_tests.py utils.py exceptions.py ./
COPY setup-venvs/ setup-venvs/
RUN set -e \
    && python setup_venvs.py \
        -t dataset/data/oracle.jsonl \
        -o dataset/data/data-success.jsonl \
        --oracle-completions experiments/completions/oracle/oracle.jsonl \
        --repos dataset/repos \
        --venvs venvs \
        --venv-setup-logs experiments/.logs/venv-setup \
        -j 8 \
    && test -f dataset/data/data-success.jsonl \
    && echo "Venv setup and oracle gate done. Tasks in data-success: $(wc -l < dataset/data/data-success.jsonl)"

# -----------------------------------------------------------------------------
# Stage 2: final image (venvs + dataset/data only; repos mounted at runtime)
# -----------------------------------------------------------------------------
FROM python:3.11-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    wget \
    build-essential \
    libx11-dev \
    xorg-dev \
    libyaml-dev \
    libglu1-mesa-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# From builder: venvs, dataset/data, and failed-venv setup logs
COPY --from=builder /app/venvs ./venvs
COPY --from=builder /app/dataset/data ./dataset/data
COPY --from=builder /app/experiments/.logs/venv-setup ./experiments/.logs/venv-setup

# App code (repos are mounted at /app/dataset/repos by docker_run_full.sh)
COPY setup_venvs.py run_tests.py utils.py exceptions.py ./
COPY setup-venvs/ setup-venvs/
COPY evaluate/ evaluate/

CMD ["/bin/bash"]
