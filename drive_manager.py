import os
import lzma
from utils import *


class DriveManager:
    def __init__(self, workspace_path):
        self.path = workspace_path
        self.repo_path = os.path.join(self.path, '.kit')

    def save_file(self, file_hash):
        folder = file_hash[:2]
        name = file_hash[2:]
        local_path = self.__get_original_file_location(file_hash)

        with open(os.path.join(self.path, local_path), 'rb') as file:
            data = bytes(file.read())
            compressed_data = lzma.compress(data)

        os.makedirs(os.path.join(self.repo_path, 'Objects', folder), exist_ok=True)

        with open(os.path.join(self.repo_path, 'Objects', folder, name), 'wb') as file:
            file.write(compressed_data)

    def save_tree(self, tree_hash: str):
        index_path = path.join(self.path, "INDEX")
        hash_folder = path.join(self.repo_path, 'Objects', tree_hash[:2], tree_hash[2:])
        os.makedirs(hash_folder)
        with open(index_path, 'r') as f:
            for line in f:
                filepath, file_hash = line.split()
                folder_name = path.split(filepath)[:-1][0]
                folder_path = path.join(hash_folder, folder_name)
                if folder_name:
                    os.makedirs(folder_path, exist_ok=True)
                with open(path.join(folder_path, path.basename(filepath)), 'w') as f:
                    f.write(file_hash)

    def save_commit(self, hash):
        pass  # TODO

    def load_file(self, file_hash):
        folder = file_hash[:2]
        name = file_hash[2:]

        with open(os.path.join(self.repo_path, 'Objects', folder, name), 'rb') as file:
            compressed_data = file.read()

        return lzma.decompress(compressed_data)

    def load_commit(self, hash):
        tree_hash = self.__get_tree_hash(hash)
        folder = tree_hash[:2]
        name = tree_hash[2:]

        pass  # TODO

    def __get_original_file_location(self, hash):
        with open(os.path.join(self.repo_path, 'INDEX'), 'r') as index:
            for file in index.readlines():
                file_path, file_hash = file.strip().split(', hash: ')
                file_path = file_path.split(': ')[1]
                file_hash = file_hash.strip()

                if file_hash == hash:
                    return file_path

        return None

    def __get_tree_hash(self, commit_hash):
        folder = commit_hash[:2]
        name = commit_hash[2:]

        with open(os.path.join(self.repo_path, 'Objects', folder, name), 'r') as commit:
            return commit.readlines()[3]
