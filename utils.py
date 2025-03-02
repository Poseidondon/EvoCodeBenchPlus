import os, json
import textwrap
import shutil
import pytest
import xml.etree.ElementTree as ET

from typing import Dict, Any, List
from collections import defaultdict


class TestResultPlugin:
    def __init__(self):
        self.results = {
            "passed": [],
            "failed": [],
            "skipped": [],
            "errors": [],
        }

    def pytest_runtest_logreport(self, report):
        """
        Hook to capture test results.
        """
        if report.when == "call":  # Only consider the test execution phase
            if report.passed:
                self.results["passed"].append(report.nodeid)
            elif report.failed:
                self.results["failed"].append(report.nodeid)
        elif report.when == "setup" and report.failed:
            self.results["errors"].append(report.nodeid)
        elif report.when == "teardown" and report.failed:
            self.results["errors"].append(report.nodeid)
        elif report.skipped:
            self.results["skipped"].append(report.nodeid)

    def get_results(self):
        """
        Return the captured results.
        """
        return self.results


def run_tests(test_path):
    """
    Run pytest and capture detailed results.
    """
    plugin = TestResultPlugin()
    pytest.main([test_path], plugins=[plugin])
    return plugin.get_results()


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


def parse_junitxml(junitxml_path: str | os.PathLike):
    tree = ET.parse(junitxml_path)
    root = tree.getroot()

    testsuite = root.find('testsuite')
    if testsuite:
        report = testsuite.attrib
        report['testcases'] = []
        for testcase in testsuite.findall('testcase'):
            report['testcases'].append(testcase.attrib)

            failure = testcase.find('failure')
            if failure is None:
                report['testcases'][-1]['failure'] = {}
            else:
                report['testcases'][-1]['failure']= failure.attrib
                report['testcases'][-1]['failure']['body'] = failure.text

            error = testcase.find('error')
            if error is None:
                report['testcases'][-1]['error'] = {}
            else:
                report['testcases'][-1]['error'] = error.attrib
                report['testcases'][-1]['error']['body'] = error.text
    else:
        report = {}
    
    return report
