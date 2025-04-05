import argparse
import pandas as pd
import json

from typing import Dict, List
from collections import defaultdict
from pprint import pprint


def parse_args():
    parser = argparse.ArgumentParser()
    # input
    parser.add_argument(
        '-r',
        '--results',
        type=str,
        default='dataset/data/data.jsonl',
        help='Path to a file with test results',
    )
    # output
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        help='Path to a file with intermediate results',
        required=True,
    )
    return parser.parse_args()


def normalize_results(results: Dict) -> Dict[str, List[bool]]:
    """
    results.json ~ {<task>: [<generation-1>, ..., <generation-n>]}
    <generation> ~ [<testsuit-1>, ..., <testsuit-n>]
    <testsuit> ~ {..., 'junitxml': {..., 'testcases': [<testcase>]}}
    """
    testcase2passes = defaultdict(list)
    for task in results:
        for generation in results[task]:
            for testsuit in generation:
                for testcase in testsuit['junitxml']['testcases']:
                    test_pass = not testcase['failure'] and not testcase['error']
                    testcase2passes[testcase['classname']].append(test_pass)
    
    return testcase2passes


if __name__ == '__main__':
    # parse args
    args = parse_args()
    print('args:')
    pprint(args.__dict__)
    print('-' * 256)

    # read results
    with open(args.results, 'r') as file:
        results = json.load(file)
    
    testcases = normalize_results(results)
    pprint(testcases)
