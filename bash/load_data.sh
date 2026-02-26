#!/bin/bash
set -e

# Create dataset directory if it doesn't exist
mkdir -p dataset/repos
# Download dataset
echo "Downloading dataset..."
wget -q --show-progress -O dataset/Source_Code.tar.gz https://huggingface.co/datasets/LJ0815/DevEval/resolve/main/Source_Code.tar.gz

# Extract the archive
echo "Extracting dataset..."
tar -xzf dataset/Source_Code.tar.gz -C dataset/
mkdir -p dataset/repos
mv dataset/Source_Code/* dataset/repos/
rmdir dataset/Source_Code
rm -f dataset/Source_Code.tar.gz

# Verify extraction
if [ "$(ls -A dataset/repos)" ]; then
    echo "Dataset extracted successfully to dataset/repos"
else
    echo "Error: Extraction failed or archive is empty" >&2
    exit 1
fi