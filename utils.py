import os, json
import textwrap
import shutil

from typing import Dict, Any, List
from collections import defaultdict


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


def load_tasks(path: str | os.PathLike) -> List[Dict[str, Any]]:
    tasks = []
    with open(path, 'r') as f:
        for line in f:
            js = json.loads(line)
            tasks.append(js)
    
    return tasks


def load_completions(path: str | os.PathLike) -> Dict[str, List[Dict[str, Any]]]:
    completions = defaultdict(list)
    with open(path, 'r') as f:
        for line in f:
            js = json.loads(line)
            completions[js['namespace']].append(js)
    
    return completions


def restore_script_backups(tasks: List[Dict[str, Any]], repos_dir: str | os.PathLike):
    for task in tasks:
        backup_path = os.path.join('.backups', task['completion_path'])
        if os.path.exists(backup_path):
            shutil.copy(backup_path, os.path.join(repos_dir, task['completion_path']))
            os.remove(backup_path)
