import subprocess
import psutil
import os
import argparse
import shutil
import json

from pprint import pprint
from typing import Mapping, Dict, Any, List
from tqdm import tqdm
from func_timeout import func_set_timeout, FunctionTimedOut

from utils import load_tasks, load_completions, restore_script_backups, adjust_indent, parse_junitxml
from exceptions import MissingRepoException, MissingVenvException, OutOfMemoryException

# TODO: parallelism
# TODO: test on oracle and nemesis


def parse_args():
    parser = argparse.ArgumentParser()
    # input
    parser.add_argument(
        '-t',
        '--tasks',
        type=str,
        default='dataset/data/data.jsonl',
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
        '-c',
        '--completions',
        type=str,
        help='Path to a file with completions',
        required=True,
    )
    # output
    parser.add_argument(
        '--tests',
        type=str,
        help='Path to a file with intermediate (or final) test results',
        required=True,
    )
    parser.add_argument(
        '-l',
        '--logs',
        type=str,
        help='Path to a directory to store pytest logs for each repo',
        required=True,
    )
    # configuration
    parser.add_argument(
        '-k', '--max-tests',
        type=int,
        default=9999,
        help='Number of tests to run using ascending idx',
    )
    parser.add_argument(
        '-r', '--restart',
        action='store_true',
        help='Forcefully restarts, even if results.json is not empty',
    )
    return parser.parse_args()


@func_set_timeout(40)
def run_test(
        repo_path: str | os.PathLike,
        venv_path: str | os.PathLike,
        logs_path: str | os.PathLike,
        test: str | os.PathLike,
):
    cmd = f'source {venv_path}/bin/activate && pytest {test} --junitxml={logs_path}'
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

    # poll process
    while True:
        pid = process.pid

        # handle memory usage
        process_memory = psutil.Process(pid).memory_info().rss
        if process_memory > 8 * 1024 * 1024 * 1024:
            process.terminate()
            process.wait()
            raise OutOfMemoryException()
        
        return_code = process.poll()
        if return_code is not None:
            stdout, stderr = process.communicate()
            process.terminate()
            process.wait()

            report = {
                'test': test,
                'return_code': return_code,
                'stdout': stdout.decode(),
                'stderr': stderr.decode(),
                'junitxml_path': None,
                'junitxml': None,
            }
            if os.path.exists(logs_path):
                report['junitxml_path'] = logs_path
                report['junitxml'] = parse_junitxml(logs_path)

            return report


def run_tests_for_repo(
        repo_path: str | os.PathLike,
        venv_path: str | os.PathLike,
        logs_path: str | os.PathLike,
        task: Dict[str, Any],
):
    # run all tests for current repository version
    test_results = []
    for test in task['tests']:
        try:
            report = run_test(repo_path, venv_path, logs_path, test)
        except (FunctionTimedOut, OutOfMemoryException) as e:
            report = {
                'test': test,
                'return_code': 5,
                'stdout': '',
                'stderr': f'{type(e).__name__}: {str(e)}',
                'junitxml_path': None,
                'junitxml': None,
            }
        
        test_results.append(report)
    
    return test_results


def run_gens_for_task(
        repos_dir: str | os.PathLike,
        venvs_dir: str | os.PathLike,
        logs_dir: str | os.PathLike,
        task: Dict[str, Any],
        gens: List[Dict[str, Any]],
        max_tests: int,
):
    # get repo name and paths
    repo_name = task['project_path']
    repo_path = os.path.join(repos_dir, repo_name)
    venv_path = os.path.join(venvs_dir, repo_name)

    # validate repo and venv
    # TODO: log this as well
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

    # no generation provided case
    if not gens:
        return [[{
            'test': '__all_tests__',
            'return_code': 5,
            'stdout': '',
            'stderr': 'No generations provided',
            'junitxml_path': None,
            'junitxml': None,
        }]]

    # sort gens
    try:
        gens.sort(key=lambda x: x['idx'])
    except KeyError:
        for ix, g in enumerate(gens):
            g['idx'] = ix
    max_idx = gens[min(len(gens) - 1, max_tests - 1)]['idx']

    results = []
    for ix, gen in enumerate(gens):
        # skip tests if max_tests is specified
        if gen['idx'] > max_idx:
            continue

        logs_path = os.path.join(logs_dir, f"{task['namespace'].replace('.', '/')}-{ix}.xml")

        # insert completion into script
        completion = adjust_indent(gen['completion'], task['indent'])
        sos, eos = task['body_position'][0] - 1, task['body_position'][1]
        with open(backup_path, 'r') as f:
            file_lines = f.readlines()
        file_lines = file_lines[:sos] + ['\n', completion, '\n'] + file_lines[eos:]
        with open(script_path, 'w') as f:
            f.write(''.join(file_lines))
        
        # run tests
        gen_result = run_tests_for_repo(repo_path, venv_path, logs_path, task)
        results.append(gen_result)

        # restore script
        shutil.copy(backup_path, script_path)
    
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
        max_tests: int = 9999,
):
    # make paths absolute if they are not already
    repos_dir = os.path.abspath(repos_dir)
    venvs_dir = os.path.abspath(venvs_dir)
    logs_dir = os.path.abspath(logs_dir)
    results_path = os.path.abspath(results_path)

    # makedirs
    os.makedirs(os.path.dirname(logs_dir), exist_ok=True)
    os.makedirs(os.path.dirname(results_path), exist_ok=True)

    # TODO: number of threads
    pass

    if restart or not os.path.exists(results_path):
        results = {}
    else:
        with open(results_path, 'r') as fp:
            results = json.load(fp)

    # restore backups if .backups exists
    if os.path.exists('.backups'):
        restore_script_backups(tasks, repos_dir)

    status = {
        'tests': 0,
        'skipped': 0,
        'errors': 0,
    }
    try:
        p_bar = tqdm(tasks, total=len(tasks), desc='Testing repositories', disable=not pbar)
        for task in p_bar:
            p_bar.set_postfix(status)
            status['tests'] += 1

            # continue on saved result
            if task['namespace'] in results:
                print(f"Skipping {task['namespace']}.")
                status['skipped'] += 1
                continue

            try:
                task_results = run_gens_for_task(
                    repos_dir,
                    venvs_dir,
                    logs_dir,
                    task,
                    completions[task['namespace']],
                    max_tests=max_tests,
                )
                results[task['namespace']] = task_results
            except MissingRepoException as e:
                print('WARNING: Missing repository!', e)
                status['errors'] += 1
            except MissingVenvException as e:
                print('WARNING: Missing venv!', e)
                status['errors'] += 1
    
    except KeyboardInterrupt as e:
        print('KeyboardInterrupt detected!')
    finally:
        print('Restoring script backups...')
        restore_script_backups(tasks, repos_dir)
        print('Restored script backups.')

        print('Testing results:')
        pprint(status)
        print('Saving results...')
        with open(results_path, 'w') as fp:
            json.dump(results, fp, indent=4, default=str)
        print(f'Saved results for {len(results)} tasks.')

    return results

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
    results = run_tests(
        tasks,
        completions,
        repos_dir=args.repos,
        venvs_dir=args.venvs,
        logs_dir=args.logs,
        results_path=args.tests,
        restart=args.restart,
        max_tests=args.max_tests
    )
