set -e

if [ -d "$venv_path" ]; then
  echo "Virtual environment already exists for $repo_path at $venv_path. Skipping creation."
else
  echo "Creating virtual environment: $venv_path..."
  python -m venv $venv_path && source $venv_path/bin/activate
  cd $repos_dir/$repo_path || exit 1

  if [ -f "setup.py" ]; then
    echo "Found setup.py"
    python setup.py install
  elif [ -f "requirements.txt" ]; then
    echo "setup.py not found. Installing from requirements.txt..."
    pip install -r requirements.txt
  else
    echo "Error: Neither setup.py nor requirements.txt found."
    exit 1
  fi

  pip install "pytest<9" pytest-runner

  deactivate
fi
