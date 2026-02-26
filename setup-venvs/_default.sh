set -e

if [ -d "$venv_path" ]; then
  echo "Virtual environment already exists for $repo_path at $venv_path. Skipping creation."
else
  echo "Creating virtual environment: $venv_path..."
  python -m venv $venv_path && source $venv_path/bin/activate
  # Pre-install packages that fix known venv failures (see venv-setup-logs/)
  pip install --upgrade 'typing-extensions>=4.14.1'
  cd $repos_dir/$repo_path || exit 1

  # Security/passpie: pre-install modern PyYAML so setup.py doesn't build PyYAML 3.11 (incompatible with Python 3.11)
  if [ "$repo_path" = "Security/passpie" ]; then
    pip install --no-cache-dir 'PyYAML>=5.1'
    echo "Installing with pip -e (passpie: avoid building old PyYAML)..."
    pip install -e .
  elif [ -f "setup.py" ]; then
    echo "Found setup.py — installing with setup.py..."
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
