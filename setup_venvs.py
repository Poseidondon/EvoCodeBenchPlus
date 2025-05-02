import subprocess
import os
import argparse
import json
import shutil

from pprint import pprint
from tqdm import tqdm
from typing import List, Dict, Set

from utils import load_tasks


def parse_args():
    parser = argparse.ArgumentParser()
    # input
    parser.add_argument(
        '-t',
        '--tasks',
        type=str,
        default='dataset/data/oracle.jsonl',
        help='Path to a file with tasks',
    )
    parser.add_argument(
        '--repos',
        type=str,
        default='dataset/repos',
        help='Path to a directory with all repositories. Must be an absolute path.',
    )
    parser.add_argument(
        '--venvs',
        type=str,
        default='venvs',
        help='Path to a directory with all venvs. Must be an absolute path.',
    )

    parser.add_argument(
        '-o',
        '--output',
        type=str,
        default='dataset/data/data-success.jsonl',
        help='Path to write a file with only successful tasks.',
    )

    return parser.parse_args()

# TODO: default policy
# TODO: catch errors?: check that requiremetns exist and all modules installed


def setup_venvs_for_tasks(tasks: List[Dict], env: Dict, pbar: bool = False) -> Set:
    progress_bar = tqdm(tasks, desc='Installing venvs', disable=pbar)
    success_tasks = []
    success_cnt = 0
    error_cnt = 0
    done_projects = {}
    
    projects = {t['project_path'] for t in tasks}
    print(f'Installing venvs for {len(projects)} projects.')

    try:
        for task in progress_bar:
            env["venv_path"] = os.path.join(env["venv_dir"], task['project_path'])
            env["repo_path"] = task['project_path']
            progress_bar.set_postfix({
                'success': success_cnt,
                'error': error_cnt,
                'repo_path': env['repo_path'],
            })

            if env['repo_path'] not in done_projects:
                # check if dir already exists
                if os.path.exists(env["venv_path"]):
                    success_cnt += 1
                    success_tasks.append(task)
                    done_projects[env['repo_path']] = 0
                    continue

                result = subprocess.run(
                    ['bash', 'setup-venvs/_default.sh'],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    # stderr=subprocess.DEVNULL,
                )

                print(f"{env['repo_path']}: {result.returncode}")
                done_projects[env['repo_path']] = result.returncode
                if result.returncode == 0:
                    success_cnt += 1
                    success_tasks.append(task)
                else:
                    error_cnt += 1
    except KeyboardInterrupt:
        print('Keyboard interrupt!')
    finally:
        success_projects = {t['project_path'] for t in success_tasks}
        error_projects = projects - success_projects
        for p in tqdm(error_projects, desc='Removing broken venvs'):
            venv_path = os.path.join(env['venv_dir'], p)
            if os.path.exists(venv_path):
                shutil.rmtree(venv_path)
    
    return success_projects


if __name__ == '__main__':
    args = parse_args()
    print('args:')
    pprint(args.__dict__)
    print('-' * 256)

    # load tasks
    print(f'Loading tasks from {args.tasks}...')
    tasks = load_tasks(args.tasks)
    print(f'Loaded {len(tasks)} tasks.')

    # setup env
    env = os.environ.copy()
    env["repos_dir"] = os.path.abspath(args.repos)
    env["venv_dir"] = os.path.abspath(args.venvs)
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = '1'
    env['PYTHONWARNINGS'] = 'ignore'

    success_projects = setup_venvs_for_tasks(tasks, env)
    success_tasks = [t for t in tasks if t['project_path'] in success_projects]

    # save successful tasks
    print(f'Saving a total of {len(success_tasks)} tasks from {len(success_projects)} successful projects...')
    with open(args.output, "w") as f:
        for item in success_tasks:
            f.write(json.dumps(item) + "\n")
