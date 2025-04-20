#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Create dataset directory if it doesn't exist
mkdir -p dataset/repos

# Download dataset
echo "Downloading dataset..."
wget -q --show-progress -O dataset/Source_Code.tar.gz https://huggingface.co/datasets/LJ0815/DevEval/resolve/main/Source_Code.tar.gz

# Extract the archive
echo "Extracting dataset..."
tar -xzf dataset/Source_Code.tar.gz -C dataset/
mv -r dataset/Source_Code/* dataset/repos/
rm -r dataset/Source_Code

# Verify extraction
if [ "$(ls -A dataset/repos)" ]; then
    echo "Dataset extracted successfully to dataset/repos"
else
    echo "Error: Extraction failed or archive is empty" >&2
    exit 1
fi

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
