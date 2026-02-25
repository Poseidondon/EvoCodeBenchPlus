import subprocess
import os
import argparse
import json
import shutil
import multiprocessing

from pprint import pprint
from tqdm import tqdm
from typing import List, Dict, Set, Tuple

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
        '-j',
        '--jobs',
        type=int,
        default=None,
        help='Number of parallel workers (default: CPU count - 1, or 1 if single CPU).',
    )
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        default='dataset/data/data-success.jsonl',
        help='Path to write a file with only successful tasks.',
    )

    return parser.parse_args()


# Top-level for pickling on spawn (Windows / some macOS)
def _setup_one_project(item: Tuple[str, str, str, str]) -> Tuple[str, int]:
    """Run venv setup for one project. Returns (project_path, returncode)."""
    project_path, repos_dir, venv_dir, script_path = item
    venv_path = os.path.join(venv_dir, project_path)
    if os.path.exists(venv_path):
        return (project_path, 0)
    env = os.environ.copy()
    env["repos_dir"] = repos_dir
    env["venv_dir"] = venv_dir
    env["venv_path"] = venv_path
    env["repo_path"] = project_path
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env["PYTHONWARNINGS"] = "ignore"
    result = subprocess.run(
        ["bash", script_path],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return (project_path, result.returncode)


def setup_venvs_for_tasks(
    tasks: List[Dict],
    env: Dict,
    script_path: str,
    jobs: int,
    pbar: bool = False,
) -> Set[str]:
    projects = sorted({t["project_path"] for t in tasks})
    print(f"Installing venvs for {len(projects)} projects (jobs={jobs}).")

    work_items = [
        (project_path, env["repos_dir"], env["venv_dir"], script_path)
        for project_path in projects
    ]

    success_projects: Set[str] = set()
    success_cnt = 0
    error_cnt = 0

    try:
        with multiprocessing.Pool(processes=jobs) as pool:
            result_iter = pool.imap_unordered(_setup_one_project, work_items, chunksize=1)
            progress_bar = tqdm(
                result_iter,
                total=len(projects),
                desc="Installing venvs",
                disable=pbar,
                unit="proj",
            )
            for project_path, returncode in progress_bar:
                print(f"{project_path}: {returncode}")
                if returncode == 0:
                    success_cnt += 1
                    success_projects.add(project_path)
                else:
                    error_cnt += 1
                progress_bar.set_postfix(
                    success=success_cnt,
                    error=error_cnt,
                    last=project_path[:30] + ("..." if len(project_path) > 30 else ""),
                )
    except KeyboardInterrupt:
        print("Keyboard interrupt!")
    finally:
        error_projects = set(projects) - success_projects
        for p in tqdm(error_projects, desc="Removing broken venvs"):
            venv_path = os.path.join(env["venv_dir"], p)
            if os.path.exists(venv_path):
                shutil.rmtree(venv_path)

    return success_projects


if __name__ == "__main__":
    args = parse_args()
    print("args:")
    pprint(args.__dict__)
    print("-" * 256)

    # load tasks
    print(f"Loading tasks from {args.tasks}...")
    tasks = load_tasks(args.tasks)
    print(f"Loaded {len(tasks)} tasks.")

    # script path (absolute so workers can run from any cwd)
    script_path = os.path.abspath("setup-venvs/_default.sh")
    if not os.path.isfile(script_path):
        raise FileNotFoundError(f"Setup script not found: {script_path}")

    # setup env
    env = os.environ.copy()
    env["repos_dir"] = os.path.abspath(args.repos)
    env["venv_dir"] = os.path.abspath(args.venvs)
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env["PYTHONWARNINGS"] = "ignore"

    jobs = args.jobs
    if jobs is None:
        n = max(1, multiprocessing.cpu_count() - 1)
        jobs = n

    success_projects = setup_venvs_for_tasks(tasks, env, script_path, jobs)
    success_tasks = [t for t in tasks if t["project_path"] in success_projects]

    # save successful tasks
    print(
        f"Saving a total of {len(success_tasks)} tasks from {len(success_projects)} successful projects..."
    )
    with open(args.output, "w") as f:
        for item in success_tasks:
            f.write(json.dumps(item) + "\n")
