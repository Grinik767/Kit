import lzma
import platform
import subprocess
from datetime import datetime
from difflib import ndiff
from distutils.dir_util import copy_tree
from os import listdir, makedirs, path, remove, rmdir, sep, walk
from random import randint

import pytest
from pytest_mock import MockerFixture
from xxhash import xxh3_128

import kit_vcs.errors as errors


class Utils:
    @staticmethod
    def check_repository_exists(method):
        def wrapper(self, *args, **kwargs):
            if not path.isdir(path.join(self.workspace_path, ".kit")):
                raise errors.RepositoryExistError("No repository found in the current directory")
            return method(self, *args, **kwargs)

        return wrapper

    @staticmethod
    def get_file_hash(abs_path: str, workspace_path: str, seed: int) -> xxh3_128:
        assert path.isfile(abs_path)
        cur_hash = xxh3_128(path.relpath(abs_path, start=workspace_path), seed=seed)
        with open(abs_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                cur_hash.update(chunk)
        return cur_hash

    @staticmethod
    def get_string_hash(string: str, seed: int) -> xxh3_128:
        return xxh3_128(string, seed=seed)

    @staticmethod
    def get_tree_hash(workspace_path: str, seed: int) -> xxh3_128:
        index_path = path.join(workspace_path, "INDEX")
        assert path.isfile(index_path) and path.basename(index_path) == "INDEX"
        cur_hash = xxh3_128('kit', seed=seed)
        with open(index_path, 'r') as f:
            for line in f:
                local_path, file_hash, diff_type = line.split(',')
                cur_hash.update(file_hash.strip())
        return cur_hash

    @staticmethod
    def bool_to_sign(value: bool) -> str:
        return "+" if value else "-"

    @staticmethod
    def sign_to_bool(value: str) -> bool:
        return True if value == '+' else False

    @staticmethod
    def get_relative_paths(dir_path: str) -> set[str]:
        relative_paths = set()

        for root, _, files in walk(dir_path):
            for file in files:
                absolute_path = path.join(root, file)
                relative_path = path.relpath(absolute_path, dir_path)
                relative_paths.add(relative_path)

        return relative_paths

    @staticmethod
    def parse_from_str_to_os_path(string_path: str):
        return path.join(*string_path.split('/'))

    @staticmethod
    def check_for_dot_path(filepath: str) -> bool:
        if path.isfile(filepath):
            return any(p.startswith('.') for p in filepath.split(sep)[:-1])
        return any(p.startswith('.') for p in filepath.split(sep))
