import argparse
import json
import os

from typing import Dict, List, Optional, Union
from collections import defaultdict
from pprint import pprint


def parse_args():
    parser = argparse.ArgumentParser()
    # input
    parser.add_argument(
        '-t',
        '--tests',
        type=str,
        default='dataset/data/data.jsonl',
        help='Path to a file with test results',
    )
    # params
    parser.add_argument(
        '-k',
        '--max-generations',
        type=int,
        default=[1],
        nargs='+',
        help='List of k values to test',
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


def pass_at_k(
        testcases: Dict[str, List[int]],
        k: int = 1,
) -> float:
    success_cnt = 0
    for test, testcase in testcases.items():
        if k <= len(testcase):
            codes = testcase[:k]
        else:
            print(f'WARNING: not enough generations for {test}!\nrequired: {k} got: {len(testcase)}')
            return float('nan')
        success_cnt += int(any(codes))
    
    return success_cnt / len(testcases)


def normalize_results(
        results: Dict,
        error_codes: Optional[Union[int, List[int]]] = None,
) -> Dict[str, List[int]]:
    """
    results.json ~ {<task>: [<generation-1>, ..., <generation-n>]}
    <generation> ~ [<testsuit-1>, ..., <testsuit-n>]
    <testsuit> ~ {..., 'junitxml': {..., 'testcases': [<testcase>]}}
    """
    # error codes
    if error_codes is None:
        error_codes = [1, 2, 3, 4, 5]
    elif isinstance(error_codes, int):
        error_codes = [error_codes]
    allowed_codes = [0] + error_codes

    # flatten
    testcase2passes = defaultdict(list)
    for task in results:
        for generation in results[task]:
            for testcase in generation:
                test_id = f"{task}-{testcase['test']}"
                testcase2passes[test_id].append(testcase['return_code'])
    
    # convert return codes
    dropped_testcases = set()
    for testcase in testcase2passes:
        testcase2passes[testcase] = [c == 0 for c in testcase2passes[testcase] if c in allowed_codes]
        if not testcase2passes[testcase]:
            dropped_testcases.add(testcase)
    if dropped_testcases:
        print(f'WARNING: droping {len(dropped_testcases)}/{len(testcase2passes)} broken testcases.')
    for t in dropped_testcases:
        del testcase2passes[t]
    
    return testcase2passes


if __name__ == '__main__':
    # parse args
    args = parse_args()
    print('args:')
    pprint(args.__dict__)
    print('-' * 256)

    # read results
    with open(args.tests, 'r') as file:
        results = json.load(file)
    
    # normalize test results
    testcases = normalize_results(results, error_codes=[1, 2, 3, 4, 5])
    print(f'Parsed {len(testcases)} testcases')

    # evaluate
    report = {}
    for k in args.max_generations:
        report[f'pass@{k}'] = pass_at_k(testcases, k=k)
    pprint(report)
    
    # save results as json
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        f.write(json.dumps(report))
