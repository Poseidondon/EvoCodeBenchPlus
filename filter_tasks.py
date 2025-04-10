import argparse
import json

from pprint import pprint
from utils import load_tasks


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
        '--tests',
        type=str,
        default='experiments/tests/oracle.json',
        help='Path to a file with test results',
    )
    parser.add_argument(
        '-c',
        '--allowed-codes',
        type=int,
        default=[0, 1],
        nargs='+',
        help='List of allowed return codes',
    )
    # output
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        help='Path to a file with fitlered tasks',
        required=True,
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    print('args:')
    pprint(args.__dict__)
    print('-' * 256)

    # load tasks
    print(f'Loading tasks from {args.tasks}...')
    tasks = load_tasks(args.tasks)
    print(f'Loaded {len(tasks)} tasks.')

    # load tests
    with open(args.tests, 'r') as file:
        tests = json.load(file)

    # filter tests
    valid_tasks = set()
    for task in tests:
        # check if any testcase has invalid return code
        task_failed = False
        generation = tests[task][0]
        for testcase in generation:
            if testcase['return_code'] not in args.allowed_codes:
                task_failed = True
                break
        
        # store valid tasks
        if not task_failed:
            valid_tasks.add(task)
    
    # filter and save tasks
    tasks = [t for t in tasks if t['namespace'] in valid_tasks]
    projects = {t['project_path'] for t in tasks}

    # save successful tasks
    print(f'Saving a total of {len(tasks)} tasks from {len(projects)} projects...')
    with open(args.output, "w") as f:
        for item in tasks:
            f.write(json.dumps(item) + "\n")
            