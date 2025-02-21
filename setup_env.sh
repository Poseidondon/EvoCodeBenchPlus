root=/home/k1shin/Projects/EvoCodeBenchPlus
data_path=$root/dataset/data/data.jsonl
repos_dir=$root/dataset/repos
venv_dir="$root/dataset/venvs"


# repo_name="contrastors"
# venv_path="$venv_dir/$repo_name"
# if [ -d "$venv_path" ]; then
#   echo "Virtual environment already exists for $repo_name at $venv_path. Skipping creation."
# else
#   echo "Creating virtual environment for $repo_name at $venv_path..."
#   python -m venv $venv_path && source $venv_path/bin/activate
#   cd $repos_dir/$repo_name || exit
#   pip install pytest pytest-runner
#   pip install -r requirements.txt
#   deactivate
# fi


repo_name="EasyVolcap"
venv_path="$venv_dir/$repo_name"
if [ -d "$venv_path" ]; then
  echo "Virtual environment already exists for $repo_name at $venv_path. Skipping creation."
else
  echo "Creating virtual environment for $repo_name at $venv_path..."
  python -m venv $venv_path && source $venv_path/bin/activate
  cd $repos_dir/$repo_name || exit
  pip install pytest pytest-runner
  pip install torch
  pip install -r requirements.txt
  deactivate
fi


repo_name="microagents"
venv_path="$venv_dir/$repo_name"
if [ -d "$venv_path" ]; then
  echo "Virtual environment already exists for $repo_name at $venv_path. Skipping creation."
else
  echo "Creating virtual environment for $repo_name at $venv_path..."
  python -m venv $venv_path && source $venv_path/bin/activate
  cd $repos_dir/$repo_name || exit
  pip install pytest pytest-runner
  pip install -r requirements.txt
  deactivate
fi
