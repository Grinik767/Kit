import os
import lzma
from utils import *


class DriveManager:
    def __init__(self, workspace_path):
        self.workspace_path = workspace_path
        self.repo_path = os.path.join(self.workspace_path, '.kit')

    def save_file(self, local_path, file_hash):
        folder = file_hash[:2]
        name = file_hash[2:]

        with open(os.path.join(self.workspace_path, local_path), 'rb') as file:
            data = bytes(file.read())
            compressed_data = lzma.compress(data)

        os.makedirs(os.path.join(self.repo_path, 'Objects', folder), exist_ok=True)

        with open(os.path.join(self.repo_path, 'Objects', folder, name), 'wb') as file:
            file.write(compressed_data)

    def save_tree(self, tree_hash: str):
        index_path = path.join(self.repo_path, "INDEX")
        hash_folder = path.join(self.repo_path, 'Objects', tree_hash[:2], tree_hash[2:])
        os.makedirs(hash_folder, exist_ok=True)
        with open(index_path, 'r') as f:
            for line in f:
                filepath, file_hash = line.split()
                folder_name = path.split(filepath)[:-1][0]
                folder_path = path.join(hash_folder, folder_name)
                if folder_name:
                    os.makedirs(folder_path, exist_ok=True)
                with open(path.join(folder_path, path.basename(filepath)), 'w') as f:
                    f.write(file_hash)

    def load_file(self, file_hash):
        folder = file_hash[:2]
        name = file_hash[2:]

        with open(os.path.join(self.repo_path, 'Objects', folder, name), 'rb') as file:
            compressed_data = file.read()

        return lzma.decompress(compressed_data)

    def save_index_files(self):
        index_path = os.path.join(self.repo_path, 'INDEX')
        with open(index_path, 'r') as index:
            for line in index.readlines():
                path, hash = line.rstrip().split(' ')
                self.save_file(path, hash)

    def write(self, local_path, data):
        with open(os.path.join(self.workspace_path, local_path), 'w') as file:
            file.write(data)

    def write_commit_data(self, commit_id, username, datetime, description, tree, parent):
        os.makedirs(os.path.join(self.repo_path, 'Objects', commit_id[:2]), exist_ok=True)
        with open(os.path.join(self.repo_path, 'Objects', commit_id[:2], commit_id[2:]), 'w') as commit:
            commit.write(f"{username}\n")
            commit.write(f"{datetime}\n")
            commit.write(f"{description}\n")
            commit.write(f"{tree}\n")
            commit.write(f"{parent}")

    def write_index_data(self, local_path: str, seed: int):
        index_path = os.path.join(self.repo_path, 'INDEX')
        file_path = os.path.join(self.workspace_path, local_path)

        with open(index_path, 'a') as index:
            if not path.isdir(file_path):
                index.write(f"{local_path} {Utils.get_file_hash(file_path, xxh3_128(seed=seed)).hexdigest()}\n")
                return

            for root, _, files in os.walk(file_path):
                for file in files:
                    file_full_path = path.join(root, file)
                    relative_path = path.relpath(file_full_path, start=self.workspace_path)
                    self.write_index_data(relative_path, seed)

    def initialize_directories(self):
        os.makedirs(self.repo_path, exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'Objects'), exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'Refs'), exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'Refs', 'heads'), exist_ok=True)

        open(os.path.join(self.repo_path, 'INDEX'), 'w').close()

    def get_head(self):
        head_path = os.path.join(self.repo_path, 'HEAD')

        if not os.path.exists(head_path):
            return None

        with open(head_path, 'r') as head_file:
            return head_file.readline()

    def get_seed(self):
        seed_path = os.path.join(self.repo_path, 'SEED')

        if not os.path.exists(seed_path):
            return None

        with open(seed_path, 'r') as head_file:
            return int(head_file.read())

    def get_last_commit_id(self, head):
        if head is None:
            return None

        with open(os.path.join(self.repo_path, 'HEAD'), 'r') as head:
            branch_path = head.readline()

        with open(os.path.join(self.repo_path, branch_path), 'r') as branch_path:
            return branch_path.readline().rstrip()

    def is_exist(self, local_path):
        return os.path.exists(os.path.join(self.workspace_path, local_path))

    def remove(self, local_path):
        os.remove(os.path.join(self.workspace_path, local_path))
