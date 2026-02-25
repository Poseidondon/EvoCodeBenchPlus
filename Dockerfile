# EvoCodeBenchPlus - code generation benchmark (MVP: repos baked in)
FROM python:3.11-bookworm

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

# Dataset: task list, oracle completions (provided in repo), and download/extract repos
COPY bash/ bash/
COPY dataset/data/oracle.jsonl dataset/data/
COPY experiments/completions/oracle/oracle.jsonl experiments/completions/oracle/oracle.jsonl
RUN set -e && bash bash/load_data.sh && test -f dataset/data/oracle.jsonl && test -d dataset/repos && test -n "$(ls -A dataset/repos)"

# App code and venv setup (oracle completions already in dataset/data)
RUN mkdir -p venvs
COPY setup_venvs.py run_tests.py utils.py exceptions.py ./
COPY setup-venvs/ setup-venvs/

# Run venv setup with oracle gate (only tasks that pass oracle go to data-success)
RUN set -e \
    && python setup_venvs.py \
        -t dataset/data/oracle.jsonl \
        -o dataset/data/data-success.jsonl \
        --oracle-completions experiments/completions/oracle/oracle.jsonl \
        --repos dataset/repos \
        --venvs venvs \
        -j 8 \
    && test -f dataset/data/data-success.jsonl \
    && echo "Venv setup and oracle gate done. Tasks in data-success: $(wc -l < dataset/data/data-success.jsonl)"

COPY evaluate/ evaluate/

CMD ["/bin/bash"]
