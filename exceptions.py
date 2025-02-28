import os
import json

from typing import Dict, Any


class MissingRepoException(Exception):
    def __init__(self, repo_path: str | os.PathLike):
        self.repo_path = repo_path

    def __str__(self):
        return f"Repository not found: {self.repo_path}"


class MissingVenvException(Exception):
    def __init__(self, venv_path: str | os.PathLike):
        self.venv_path = venv_path

    def __str__(self):
        return f"Venv not found: {self.venv_path}"


class OutOfMemoryException(Exception):
    def __init__(self):
        pass

    def __str__(self):
        return "Out of memory"


class TestException(Exception):
    def __init__(self, error: Dict[str, Any]):
        self.error = error

    def __str__(self):
        return "pytest error:\n" + json.dumps(self.error, indent=4)
