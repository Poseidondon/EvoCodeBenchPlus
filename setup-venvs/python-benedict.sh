repo_path="Text-Processing/python-benedict"
venv_path="$venv_dir/$repo_path"
if [ -d "$venv_path" ]; then
  echo "Virtual environment already exists for $repo_path at $venv_path. Skipping creation."
else
  echo "Creating virtual environment: $venv_path..."
  python -m venv $venv_path && source $venv_path/bin/activate
  cd $repos_dir/$repo_path || exit
  pip install pytest pytest-runner
  pip install -r requirements.txt
  deactivate
fi
