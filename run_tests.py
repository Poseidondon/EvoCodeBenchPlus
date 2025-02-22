import subprocess
import psutil
import os
import numpy as np
import func_timeout
import textwrap
import argparse
import shutil
from pprint import pprint
from typing import Mapping, Dict, Any, List
from subprocess import run
from tqdm import tqdm
from func_timeout import func_set_timeout, FunctionTimedOut

from utils import load_tasks, load_completions, restore_script_backups, adjust_indent
from exceptions import MissingRepoException, MissingVenvException, OutOfMemoryException

# TODO: fix functions
# TODO: parallelism
# TODO: save progress on exit
# TODO: test on oracle and nemesis


def parse_args():
    parser = argparse.ArgumentParser()
    # input
    parser.add_argument(
        '--tasks',
        type=str,
        default='dataset/data/data.jsonl',
        help='Path to a file with tasks',
    )
    parser.add_argument(
        '--repos',
        type=str,
        help='Path to a directory with all repositories. Must be an absolute path.',
    )
    parser.add_argument(
        '--venvs',
        type=str,
        help='Path to a directory with all venvs. Must be an absolute path.',
    )
    parser.add_argument(
        '--completions',
        type=str,
        help='Path to a file with completions',
    )
    # output
    parser.add_argument(
        '--results',
        type=str,
        help='Path to a file with intermediate results',
    )
    parser.add_argument(
        '--logs',
        type=str,
        help='Path to a directory to store stdout and stderr for each repo',
    )
    # configuration
    parser.add_argument(
        '-r', '--restart',
        action='store_true',
        help='Forcefully restarts, even if results.jsonl is not empty',
    )
    return parser.parse_args()


@func_set_timeout(30)
def run_test(repo_path: str | os.PathLike, venv_path: str | os.PathLike, test: str | os.PathLike):
    cmd = f'source {venv_path}/bin/activate && pytest {test}'
    process = subprocess.Popen(
        ['bash', '-c', cmd],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={
            **os.environ,
            'PYTHONPATH': f'{repo_path}:{os.environ.get("PYTHONPATH", "")}'
        },
    )
    try:
        while True:
            pid = process.pid

            # handle memory usage
            process_memory = psutil.Process(pid).memory_info().rss
            if process_memory > 4 * 1024 * 1024 * 1024:
                process.terminate()
                process.wait()
                return OutOfMemoryException()
            
            return_code = process.poll()
            if return_code is not None:
                stdout, stderr = process.communicate()
                if return_code != 0:
                    process.terminate()
                    process.wait()
                    error = {
                        'return_code': return_code,
                        'stdout': stdout.decode(),
                        'stderr': stderr.decode(),
                    }
                    print(error['stdout'])
                    return error
                else:
                    return True
    except Exception as e:
        process.terminate()
        process.wait()
        return e


def run_tests_for_repo(
        repo_path: str | os.PathLike,
        venv_path: str | os.PathLike,
        task: Dict[str, Any],
):
    # run all tests for current repository version
    test_results = []
    for test in task['tests']:
        try:
            res = run_test(repo_path, venv_path, test)
            test_results.append(res)
        except Exception as e:
            test_results.append(e)
    
    return test_results


def run_gens_for_task(
        repos_dir: str | os.PathLike,
        venvs_dir: str | os.PathLike,
        task: Dict[str, Any],
        gens: List[Dict[str, Any]],
):
    # get repo name and paths
    repo_name = task['completion_path'].split('/')[0]
    repo_path = os.path.join(repos_dir, repo_name)
    venv_path = os.path.join(venvs_dir, repo_name)

    # validate repo and venv
    if not os.path.exists(repo_path):
        raise MissingRepoException(repo_path)
    if not os.path.exists(venv_path):
        raise MissingVenvException(venv_path)

    # make script backup
    script_path = os.path.join(repos_dir, task['completion_path'])
    backup_path = os.path.join('.backups', task['completion_path'])
    backup_dir = os.path.dirname(backup_path)
    os.makedirs(backup_dir, exist_ok=True)
    shutil.copy(script_path, backup_path)

    results = []
    for gen in gens:
        # insert completion into script
        completion = adjust_indent(gen['completion'], task['indent'])
        sos, eos = task['body_position'][0] - 1, task['body_position'][1]
        with open(backup_path, 'r') as f:
            file_lines = f.readlines()
        file_lines = file_lines[:sos] + ['\n', completion, '\n'] + file_lines[eos:]
        with open(script_path, 'w') as f:
            f.write(''.join(file_lines))
        
        # run tests
        gen_result = run_tests_for_repo(repo_path, venv_path, task)
        results.append(gen_result)

        # restore script
        shutil.copy(backup_path, script_path)
        # clean up
        os.remove(backup_path)
    
    return results


def run_tests(
        tasks: Mapping[str, Dict[str, Any]],
        completions: Mapping[str, Dict[str, Any]],
        repos_dir: str | os.PathLike,
        venvs_dir: str | os.PathLike,
        logs_dir: str | os.PathLike,
        results_path: str | os.PathLike,
        restart: bool = False,
        njobs: int = -1,
        pbar: bool = True,
):
    # Validate paths are absolute
    if not os.path.isabs(repos_dir):
        raise ValueError(f"repos_dir must be an absolute path, got: {repos_dir}")
    if not os.path.isabs(venvs_dir):
        raise ValueError(f"venvs_dir must be an absolute path, got: {venvs_dir}")

    # TODO: number of threads
    pass

    # TODO: read intermediate results
    results = {}

    # restore backups if .backups exists
    if os.path.exists('.backups'):
        restore_script_backups(tasks, repos_dir)

    try:
        p_bar = tqdm(tasks, total=len(tasks), desc='Testing repositories', disable=not pbar)
        p_bar.set_postfix({
            'tests_pass': 0,
            'tests_error': 0,
            'repos_pass': 0,
            'repos_error': 0,
        })
        for task in p_bar:
            # TODO: append results to results dict
            try:
                task_results = run_gens_for_task(repos_dir, venvs_dir, task, completions[task['namespace']])
                print(task_results)
            except MissingRepoException as e:
                print('WARNING: Missing repository!', e)
            except MissingVenvException as e:
                print('WARNING: Missing venv!', e)
    
    except KeyboardInterrupt as e:
        print('KeyboardInterrupt detected!')

        print('Restoring script backups...')
        restore_script_backups(tasks, repos_dir)

        # TODO: save intermediate results
        pass

if __name__ == '__main__':
    args = parse_args()
    print('args:')
    pprint(args.__dict__)
    print('-' * 256)

    # load tasks
    print(f'Loading tasks from {args.tasks}...')
    tasks = load_tasks(args.tasks)
    print(f'Loaded {len(tasks)} tasks.')

    # load completions
    print(f'Loading completions from {args.completions}...')
    completions = load_completions(args.completions)
    print(f'Loaded {len(completions)} completions.')

    # run tasks
    run_tests(
        tasks,
        completions,
        repos_dir=args.repos,
        venvs_dir=args.venvs,
        logs_dir=args.logs,
        results_path=args.results,
        restart=args.restart,
    )
