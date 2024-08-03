from abc import ABC, abstractmethod
from os import path, walk, remove, rmdir, makedirs
from xxhash import xxh3_128
import errors
from distutils.dir_util import copy_tree
import pytest


class Utils:
    @staticmethod
    def get_tree_diff(tree1_path, tree2_path):
        result = []
        added_files, removed_files, changed_files = Utils.__compare_trees(tree1_path, tree2_path)

        for file in sorted(added_files):
            result.append(f"+;{file}")

        for file in sorted(changed_files):
            result.append(f"~;{file}")

        for file in sorted(removed_files):
            result.append(f"-;{file}")

        return result

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
    def __get_relative_paths(dir_path):
        relative_paths = set()

        for root, _, files in walk(dir_path):
            for file in files:
                absolute_path = path.join(root, file)
                relative_path = path.relpath(absolute_path, dir_path)
                relative_paths.add(relative_path)

        return relative_paths

    @staticmethod
    def __read_file_content(file_path: str):
        with open(file_path, 'rb') as file:
            return file.read()

    @staticmethod
    def __compare_trees(tree1, tree2):
        dir1_files = Utils.__get_relative_paths(tree1)
        dir2_files = Utils.__get_relative_paths(tree2)

        removed_files = dir1_files - dir2_files
        added_files = dir2_files - dir1_files

        common_files = dir1_files & dir2_files
        changed_files = set()

        for file in common_files:
            file1 = path.join(tree1, file)
            file2 = path.join(tree2, file)

            if Utils.__read_file_content(file1) != Utils.__read_file_content(file2):
                changed_files.add(file)

        return added_files, removed_files, changed_files
