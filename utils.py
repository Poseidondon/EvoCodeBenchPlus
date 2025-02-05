import os, json
import textwrap

from typing import Mapping, Dict, Any


def load_json_data(input_file: str):
    data = []
    with open(input_file, 'r') as f:
        for line in f:
            js = json.loads(line)
            data.append(js)
    return data


def count_indent(args, data):
    code_file_path = os.path.join(args.source_code_root, data['completion_path'])
    with open(code_file_path, 'r') as f:
        lines = f.readlines()
    body_first_line = lines[data['body_position'][0] - 1]
    indent = len(body_first_line) - len(textwrap.dedent(body_first_line))
    return indent


def adjust_indent(code, new_indent):
    # remove original indentation
    dedented_code = textwrap.dedent(code)
    # add new indentation
    indented_code = textwrap.indent(dedented_code, ' ' * new_indent)
    return indented_code


def load_namespace2data(path: str | os.PathLike) -> Mapping[str, Dict[str, Any]]:
    namespace2data = {}
    with open(path, 'r') as f:
        for line in f:
            js = json.loads(line)
            namespace = js['namespace']
            if namespace not in namespace2data:
                namespace2data[namespace] = js
            else:
                print('WARNING: dropping duplicate namespace!', namespace)

    return namespace2data
