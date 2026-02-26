import subprocess
import os
import argparse
import json
import shutil
import multiprocessing

from pprint import pprint
from tqdm import tqdm
from typing import List, Dict, Set, Tuple

from utils import load_tasks, load_completions
from run_tests import run_tests, task_passed


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
        help='Path to write a file with only tasks that passed oracle tests.',
    )
    parser.add_argument(
        '--oracle-logs',
        type=str,
        default='experiments/.logs/oracle-setup',
        help='Directory for pytest logs during oracle run.',
    )
    parser.add_argument(
        '--oracle-results',
        type=str,
        default='dataset/data/oracle-setup-results.json',
        help='Path to store oracle test results (per-namespace).',
    )
    parser.add_argument(
        '--oracle-completions',
        type=str,
        required=True,
        help='Path to oracle completions JSONL.',
    )
    parser.add_argument(
        '--no-oracle',
        action='store_true',
        help='Skip oracle test run: write all venv-success tasks to output (previous behavior).',
    )
    parser.add_argument(
        '--venv-setup-logs',
        type=str,
        default=None,
        help='Directory to write stdout/stderr logs for failed venv setups (one file per failed project).',
    )

    return parser.parse_args()


# Top-level for pickling on spawn (Windows / some macOS)
def _setup_one_project(item: Tuple[str, str, str, str, str | None]) -> Tuple[str, int]:
    """Run venv setup for one project. Returns (project_path, returncode)."""
    project_path, repos_dir, venv_dir, script_path, log_dir = item
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
    capture_output = log_dir is not None
    result = subprocess.run(
        ["bash", script_path],
        env=env,
        stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
        stderr=subprocess.STDOUT if capture_output else subprocess.DEVNULL,
        text=True,
    )
    if capture_output and result.returncode != 0 and result.stdout:
        safe_name = project_path.replace("/", "_").replace("\\", "_")
        log_path = os.path.join(log_dir, f"{safe_name}.log")
        try:
            with open(log_path, "w") as f:
                f.write(f"# project_path: {project_path}\n")
                f.write(f"# returncode: {result.returncode}\n")
                f.write("-" * 80 + "\n")
                f.write(result.stdout)
        except OSError:
            pass
    return (project_path, result.returncode)


def setup_venvs_for_tasks(
    tasks: List[Dict],
    env: Dict,
    script_path: str,
    jobs: int,
    pbar: bool = False,
    venv_setup_logs_dir: str | None = None,
) -> Set[str]:
    projects = sorted({t["project_path"] for t in tasks})
    print(f"Installing venvs for {len(projects)} projects (jobs={jobs}).")
    if venv_setup_logs_dir:
        os.makedirs(venv_setup_logs_dir, exist_ok=True)
        print(f"Failed venv logs will be written to: {os.path.abspath(venv_setup_logs_dir)}")

    work_items = [
        (project_path, env["repos_dir"], env["venv_dir"], script_path, venv_setup_logs_dir)
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
        if error_cnt and venv_setup_logs_dir:
            print(f"Failed venv logs written to: {os.path.abspath(venv_setup_logs_dir)} ({error_cnt} files)")

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

    success_projects = setup_venvs_for_tasks(
        tasks, env, script_path, jobs, venv_setup_logs_dir=args.venv_setup_logs
    )
    success_tasks = [t for t in tasks if t["project_path"] in success_projects]

    if args.no_oracle:
        # Previous behavior: save all tasks with successful venv setup
        final_tasks = success_tasks
        print(
            f"Saving {len(final_tasks)} tasks (venv success only, oracle skipped)..."
        )
    else:
        # Run oracle tests; only add to data-success if tests passed
        repos_dir = env["repos_dir"]
        venvs_dir = env["venv_dir"]
        os.makedirs(os.path.dirname(args.oracle_logs) or ".", exist_ok=True)
        os.makedirs(os.path.dirname(args.oracle_results) or ".", exist_ok=True)

        if not os.path.isfile(args.oracle_completions):
            raise FileNotFoundError(
                f"Oracle completions file not found: {args.oracle_completions}"
            )
        print(f"Loading oracle completions from {args.oracle_completions}...")
        completions = load_completions(args.oracle_completions)

        print(f"Running oracle tests for {len(success_tasks)} tasks...")
        run_tests(
            success_tasks,
            completions,
            repos_dir=repos_dir,
            venvs_dir=venvs_dir,
            logs_dir=args.oracle_logs,
            results_path=args.oracle_results,
            restart=True,
            njobs=jobs,
            pbar=True,
            max_tests=1,
            signature_completed=False,
        )

        with open(args.oracle_results) as f:
            results = json.load(f)
        final_tasks = [
            t for t in success_tasks
            if task_passed(results.get(t["namespace"], []))
        ]
        failed_count = len(success_tasks) - len(final_tasks)
        print(
            f"Oracle passed: {len(final_tasks)} tasks, failed: {failed_count} (excluded from output)."
        )

    with open(args.output, "w") as f:
        for item in final_tasks:
            f.write(json.dumps(item) + "\n")
    print(f"Wrote {len(final_tasks)} tasks to {args.output}.")
