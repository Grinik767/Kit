import os
import lzma
import subprocess
import platform
from utils import *


class DriveManager:
    def __init__(self, workspace_path):
        self.workspace_path = workspace_path
        self.repo_path = os.path.join(self.workspace_path, '.kit')
        self.index_path = os.path.join(self.repo_path, 'INDEX')
        self.index_hashes = self.get_index_hashes()

    def save_file(self, local_path, file_hash):
        folder = file_hash[:2]
        name = file_hash[2:]

        with open(os.path.join(self.workspace_path, local_path), 'rb') as file:
            data = bytes(file.read())
            compressed_data = lzma.compress(data)

        os.makedirs(os.path.join(self.repo_path, 'objects', folder), exist_ok=True)

        with open(os.path.join(self.repo_path, 'objects', folder, name), 'wb') as file:
            file.write(compressed_data)

    def save_tree(self, tree_hash: str, prev_tree_hash: str):
        prev_tree_path = path.join(self.repo_path, 'objects', prev_tree_hash[:2], prev_tree_hash[2:])
        hash_folder = path.join(self.repo_path, 'objects', tree_hash[:2], tree_hash[2:])
        os.makedirs(hash_folder)
        if path.exists(prev_tree_path):
            copy_tree(prev_tree_path, hash_folder)
        with open(self.index_path, 'r') as f:
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

        with open(os.path.abspath(os.path.join(self.repo_path, 'objects', folder, name)), 'rb') as file:
            compressed_data = file.read()

        return lzma.decompress(compressed_data)

    def save_files_from_index(self):
        with open(self.index_path, 'r') as index:
            for line in index.readlines():
                file_path, cur_hash = line.rstrip().split(' ')
                self.save_file(file_path, cur_hash)

    def write(self, local_path, data):
        with open(os.path.join(self.workspace_path, local_path), 'w') as file:
            file.write(data)

    def read(self, local_path):
        with open(os.path.join(self.workspace_path, local_path), 'r') as file:
            return file.read()

    def write_commit_data(self, commit_id, username, datetime, description, tree, parent):
        os.makedirs(os.path.join(self.repo_path, 'objects', commit_id[:2]), exist_ok=True)
        with open(os.path.join(self.repo_path, 'objects', commit_id[:2], commit_id[2:]), 'w') as commit:
            commit.write(f"{username}\n{datetime}\n{description}\n{tree}\n{parent}")

    def write_index_data(self, local_path: str, prev_tree_hash: str, seed: int):
        file_path = os.path.join(self.workspace_path, local_path)
        with open(self.index_path, 'a') as index:
            if not path.isdir(file_path):
                rel_path = path.relpath(file_path, start=self.workspace_path)
                filehash = Utils.get_file_hash(file_path, self.workspace_path, seed).hexdigest()
                prev_tree_path = path.join(self.repo_path, 'objects', prev_tree_hash[:2], prev_tree_hash[2:])
                prev_filehash = None
                if path.exists(path.join(prev_tree_path, rel_path)):
                    with open(path.join(prev_tree_path, rel_path), 'r') as f:
                        prev_filehash = f.read().strip()
                if filehash not in self.index_hashes and (prev_filehash is None or prev_filehash != filehash):
                    self.index_hashes[filehash] = rel_path
                    index.write(f"{rel_path} {filehash}\n")
                return

            for root, _, files in os.walk(file_path):
                for file in files:
                    file_full_path = path.join(root, file)

                    relative_path = path.relpath(file_full_path, start=self.workspace_path)
                    self.write_index_data(relative_path, prev_tree_hash, seed)

    def load_tree_files(self, tree_hash: str):
        if not tree_hash:
            return
        tree_path = path.join(self.repo_path, 'objects', tree_hash[:2], tree_hash[2:])
        for root, dirs, files in walk(tree_path):
            rel_path = path.relpath(root, start=tree_path)
            makedirs(rel_path, exist_ok=True)
            for file in files:
                with open(path.join(root, file), 'r') as f:
                    filehash = f.read().strip()
                with open(path.join(self.workspace_path, rel_path, file), 'wb') as f:
                    f.write(self.load_file(filehash))

    def delete_tree_files(self, tree_hash: str):
        if not tree_hash:
            return
        tree_path = path.join(self.repo_path, 'objects', tree_hash[:2], tree_hash[2:])
        for root, dirs, files in walk(tree_path, topdown=False):
            for file in files:
                full_path = path.join(self.workspace_path, path.relpath(path.join(root, file), start=tree_path))
                print(full_path)
                if path.exists(full_path):
                    remove(full_path)
            for directory in dirs:
                full_path = path.join(self.workspace_path, path.relpath(path.join(root, directory), start=tree_path))
                print(full_path)
                if path.exists(full_path):
                    rmdir(full_path)

    def get_index_hashes(self) -> dict[str: str]:
        result = {}
        if not path.exists(self.index_path):
            return result
        with open(self.index_path, 'r') as f:
            for line in f:
                filepath, filehash = line.split()
                result[filehash] = filepath
        return result

    def initialize_directories(self):
        os.makedirs(self.repo_path, exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'objects'), exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'refs'), exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'refs', 'heads'), exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'refs', 'tags'), exist_ok=True)

        open(os.path.join(self.repo_path, 'INDEX'), 'w').close()

        if platform.system() == "Windows":
            subprocess.run(['attrib', '+H', self.repo_path], check=True)

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

        if path.exists(os.path.join(self.repo_path, 'objects', head[:2], head[2:])):
            return head

        with open(os.path.join(self.repo_path, 'HEAD'), 'r') as head:
            branch_path = head.readline()

        with open(os.path.join(self.repo_path, branch_path), 'r') as branch:
            return branch.readline().rstrip()

    def get_commit_tree_hash(self, commit_id: str):
        commit_path = path.join(self.repo_path, 'objects', commit_id[:2], commit_id[2:])
        if not path.exists(commit_path):
            return
        with open(commit_path, 'r') as f:
            return f.readlines()[-2][:-1]

    def is_exist(self, local_path):
        return os.path.exists(os.path.join(self.workspace_path, local_path))

    def delete_if_empty_file(self, local_path):
        full_path = path.join(self.workspace_path, local_path)
        if path.getsize(full_path) == 0:
            remove(full_path)

    def remove(self, local_path):
        os.remove(os.path.join(self.workspace_path, local_path))


if __name__ == '__main__':
    pass
