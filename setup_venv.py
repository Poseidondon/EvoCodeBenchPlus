import subprocess
import os

# globals
ENV = os.environ.copy()
ROOT = '/home/k1shin/EvoCodeBenchPlus'
ENV["repos_dir"] = os.path.join(ROOT, 'dataset/repos')
ENV["venv_dir"] = os.path.join(ROOT, 'venvs')

if __name__ == '__main__':
    subprocess.run(['bash', 'setup-venvs/python-benedict.sh'], env=ENV)
