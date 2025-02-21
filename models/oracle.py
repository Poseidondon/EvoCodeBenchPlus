import json
import os

from argparse import ArgumentParser
from pathlib import Path


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('--data_path', default='dataset/data/data.jsonl', help='Path to the data.jsonl file')
    parser.add_argument('--source_code_root', default='dataset/repos', help='Path to the source code directory')
    parser.add_argument('--output_file', required=True, type=str, help='Path to the completion file (output file)')
    return parser.parse_args()


def main():
    args = parse_args()

    # read data
    print('Reading data...')
    data = []
    with open(args.data_path, 'r') as f:
        for line in f:
            js = json.loads(line)
            data.append(js)
    print(f'Read {len(data)} tasks.')

    # write completion file
    print(f'Writing output to {args.output_file}...')
    os.makedirs(Path(args.output_file).parent, exist_ok=True)
    with open(args.output_file, 'w') as out_f:
        for task in data:
            with open(f"{args.source_code_root}/{task['completion_path']}", 'r') as src_f:
                lines = src_f.read().split('\n')
                start, end = task['body_position']
                start -= 1
                body = '\n'.join(lines[start:end])
                pred = {'namespace': task['namespace'], 'completion': body}
                out_f.write(json.dumps(pred) + '\n')
    print(f'Oracle completion successfully wrote.')


if __name__ == '__main__':
    main()
