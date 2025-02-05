import json
import subprocess
import psutil
import os
import numpy as np
import func_timeout
import textwrap
import argparse

from pprint import pprint
from typing import Mapping, Dict, Any
from subprocess import run
from tqdm import tqdm
from func_timeout import func_set_timeout

from utils import load_namespace2data

# TODO: fix functions
# TODO: parallelism
# TODO: save progress on exit
# TODO: test on oracle and nemesis
# TODO: refactor myenv different file for each setup


def parse_args():
    parser = argparse.ArgumentParser()
    # input
    parser.add_argument(
        '--tasks',
        type=str,
        default='data/data.jsonl',
        help='Path to a file with tasks',
    )
    parser.add_argument(
        '--repos',
        type=str,
        default='Source_Code',
        help='Path to a directory with all repositories',
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


def adjust_indent(code, new_indent):
    # remove original indentation
    dedented_code = textwrap.dedent(code)
    # add new indentation
    indented_code = textwrap.indent(dedented_code, ' ' * new_indent)
    return indented_code


@func_set_timeout(20)
def execution_tests(test, project_path):
    command = "source myenv/bin/activate && pytest " + test
    env = os.environ.copy()
    env['PATH'] = f"/home/k1shin/EvoCodeBench/{project_path}:{env['PATH']}"
    env['PYTHONPATH'] = f"{project_path}:{env.get('PYTHONPATH', '')}"
    print(f"/home/k1shin/EvoCodeBench/{project_path}:{env['PATH']}")
    process = subprocess.Popen(['bash', '-c', command], cwd=project_path, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env=env)
    try:
        while True:
            process_id = process.pid
            process_memory = psutil.Process(process_id).memory_info().rss
            if process_memory > 5 * 1024 * 1024 * 1024:  # 5GB memory usage per test
                print('OOM')
                process.terminate()
                process.wait()
                return False  # Out of Memory
            return_code = process.poll()
            if return_code is not None:
                if return_code != 0:
                    stdout, stderr = process.communicate()
                    print('return_code:', return_code)
                    print('stdout:', stdout.decode("utf-8"))
                    print('stderr:', stderr.decode("utf-8"))
                    process.terminate()
                    process.wait()
                    return False  # Execution Error
                else:
                    break
    except Exception as e:
        stdout, stderr = process.communicate()
        print('stdout:', stdout.decode("utf-8"))
        print('stderr:', stderr.decode("utf-8"))
        process.terminate()
        process.wait()
        return False  # Other Error
    finally:
        process.terminate()
        process.wait()
    print('good')
    return True  # Pass


def SetUp_evaluation(args, data, completion):
    completion_path = os.path.join(args.source_code_path, data['completion_path'])
    head_tail = os.path.split(completion_path)
    completion_tmp_path = os.path.join(head_tail[0], 'tmp_' + head_tail[1])

    # rename the original completion file as tmp_completion
    run(['cp', completion_path, completion_tmp_path])

    # write the new completion file
    sos, eos = data['body_position'][0] - 1, data['body_position'][1]
    with open(completion_path, 'r') as f:
        file_lines = f.readlines()
    file_lines = file_lines[:sos] + ['\n', completion, '\n'] + file_lines[eos:]
    with open(completion_path, 'w') as f:
        f.write(''.join(file_lines))


def TearDown_evaluation(args, data):
    completion_path = os.path.join(args.source_code_root, data['completion_path'])
    head_tail = os.path.split(completion_path)
    completion_tmp_path = os.path.join(head_tail[0], 'tmp_' + head_tail[1])
    run(['mv', completion_tmp_path, completion_path])


def check_correctness(args, data):
    completion = data['completion']
    if completion == "    pass\n":
        return 'Fail'
    completion = adjust_indent(completion, data['indent'])

    SetUp_evaluation(args, data, completion)
    project_name = data['completion_path'].split('/')[0]
    project_path = os.path.join(args.source_code_root, project_name)
    flag = 'Pass'
    for test in data['tests']:
        try:
            result = execution_tests(test, project_path)
            if not result:
                flag = 'Fail'
                break
        except func_timeout.exceptions.FunctionTimedOut:
            flag = 'Fail'
            break
    TearDown_evaluation(args, data)
    return flag


def run_tests(
        tasks: Mapping[str, Dict[str, Any]],
        completions: Mapping[str, Dict[str, Any]],
        repos_dir: str | os.PathLike,
        logs_dir: str | os.PathLike,
        results_path: str | os.PathLike,
        restart: bool = False,
        njobs: int = -1,
        pbar: bool = True,
):
    # TODO: number of threads
    pass

    # TODO: read intermediate results
    results = {}

    try:
        p_bar = tqdm(tasks.items(), total=len(tasks), desc='Testing repositories', disable=not pbar)
        p_bar.set_postfix({
            'tests_pass': 0,
            'tests_error': 0,
            'repos_pass': 0,
            'repos_error': 0,
        })
        for namespace, task in p_bar:
            pass
    except KeyboardInterrupt as e:
        pass

    # iterate through the output data
    # with open(args.log_file, 'a') as f:
    #     for output in tqdm(todo_output_data):
    #         namespace = output['namespace']
    #         if namespace in namespace2task:
    #             data = namespace2task[namespace]
    #             data['completion'] = output['completion']
    #             result = check_correctness(args, data)
    #             output['Result'] = result
    #             f.write(json.dumps(output) + '\n')
    #             f.flush()
    #
    # report_results(args, namespace2task)


if __name__ == '__main__':
    args = parse_args()
    print('args:')
    pprint(args.__dict__)
    print('-' * 256)

    # load tasks
    print(f'Loading tasks from {args.tasks}...')
    tasks = load_namespace2data(args.tasks)
    print(f'Loaded {len(tasks)} tasks.')

    # load completions
    print(f'Loading completions from {args.completions}...')
    completions = load_namespace2data(args.completions)
    print(f'Loaded {len(completions)} completions.')

    # run tasks
    run_tests(
        tasks,
        completions,
        repos_dir=args.repos,
        logs_dir=args.logs,
        results_path=args.results,
        restart=args.restart,
    )
