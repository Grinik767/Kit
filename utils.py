from abc import ABC, abstractmethod
from os import path, walk
from xxhash import xxh3_128
import pytest


class Utils:
    @staticmethod
    def get_file_hash(local_path: str, cur_hash: xxh3_128) -> xxh3_128:
        assert path.isfile(local_path)
        cur_hash.update(local_path)
        with open(local_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                cur_hash.update(chunk)
        return cur_hash

    @staticmethod
    def get_dir_hash(local_path: str, cur_hash: xxh3_128) -> xxh3_128:
        assert path.isdir(local_path)
        for root, dirs, files in walk(local_path):
            for file in files:
                cur_hash = Utils.get_file_hash(path.join(root, file), cur_hash)
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


if __name__ == '__main__':
    pass
