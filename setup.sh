#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# load repositories
echo "Loading dataset"
if [ -f bash/load_data.sh ]; then
    bash bash/load_data.sh
else
    echo "Error: load_data.sh not found"
    exit 1
fi

echo "Setup completed successfully"
