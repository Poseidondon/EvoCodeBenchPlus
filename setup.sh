#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# conda environment
# conda create --name EvoCodeBench python=3.11
# conda activate EvoCodeBench
pip install pytest
pip install numpy
pip install tqdm
pip install tiktoken
pip install psutil
pip install func_timeout

# load repositories
echo "Loading dataset"
if [ -f bash/load_data.sh ]; then
    bash bash/load_data.sh
else
    echo "Error: load_data.sh not found"
    exit 1

# Setup virtual environments
echo "Setting up virtual environments..."
if [ -f bash/prepare_env.sh ]; then
    bash bash/prepare_env.sh
else
    echo "Error: prepare_env.sh not found" >&2
    exit 1
fi

if [ -f setup_venvs.py ]; then
    python setup_venvs.py
else
    echo "Error: setup_venvs.py not found" >&2
    exit 1
fi

echo "Setup completed successfully"
