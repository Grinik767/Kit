from abc import ABC, abstractmethod
from os import path, walk, remove, rmdir, makedirs
from xxhash import xxh3_128
import errors
from distutils.dir_util import copy_tree
import pytest


class Utils:
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
                local_path, file_hash = line.split()
                cur_hash.update(file_hash)
        return cur_hash
