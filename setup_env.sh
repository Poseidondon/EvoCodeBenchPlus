Root=/home/k1shin/EvoCodeBench
Data_Path=$Root/data.jsonl
Source_Code_Root=$Root/Source_Code


# Setup the execution environment for contrastors
repo_name="contrastors"
venv_dir="$Root/venvs/$repo_name"
# Check if the virtual environment directory already exists
if [ -d "$venv_dir" ]; then
  echo "Virtual environment already exists for $repo_name at $venv_dir. Skipping creation."
else
  # Create the virtual environment if it doesn't exist
  echo "Creating virtual environment for $repo_name at $venv_dir..."
  python -m venv $venv_dir && source $venv_dir/bin/activate
  cd $Root/Source_Code/$repo_name || exit
  pip install pytest pytest-runner
  pip install -r requirements.txt
  deactivate
fi
