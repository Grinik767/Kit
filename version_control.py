import os
from drive_manager import DriveManager
from errors.NothingToCommitError import NothingToCommitError
from errors.RepositoryAlreadyExistError import RepositoryAlreadyExistError
from errors.BranchAlreadyExistError import BranchAlreadyExitsError
from utils import Utils
from xxhash import xxh3_128
from random import randint
from datetime import datetime


class VersionControl:
    def __init__(self, path, username):
        self.path = path
        self.repo_path = os.path.abspath(os.path.join(path, ".kit"))
        self.username = username
        self.drive = DriveManager(path)
        self.last_commit_id = VersionControl.__get_last_commit_id(self.repo_path)
        self.seed = VersionControl.__get_seed(self.repo_path)

    def init(self):
        if os.path.exists(self.repo_path):
            raise RepositoryAlreadyExistError

        self.last_commit_id = None
        self.seed = randint(10000000, 99999999)
        self.__create_directories()
        self.commit("initial commit")

        with open(os.path.join(self.repo_path, 'SEED'), 'w') as seed:
            seed.write(f'seed: {self.seed}\n')

        with open(os.path.join(self.repo_path, 'Refs', 'heads', 'main'), 'w') as main:
            main.write(f'ref: {self.last_commit_id}\n')

        self.__update_head()

    def add(self, local_path: str):
        index_path = os.path.join(self.repo_path, 'INDEX')
        file_path = os.path.join(self.path, local_path)

        with open(index_path, 'a') as index:
            index.write(f"path: {local_path}, hash: {Utils.get_file_hash(file_path, xxh3_128(seed=self.seed)).hexdigest()}\n")

    def commit(self, description: str):
        index_path = os.path.join(self.repo_path, 'index')

        if not os.path.exists(index_path) and self.last_commit_id is not None:
            raise NothingToCommitError

        commit_id = xxh3_128(self.username + description + datetime.now().isoformat(), seed=self.seed).hexdigest()
        objects_path = os.path.join(self.repo_path, 'Objects')
        os.makedirs(os.path.join(objects_path, commit_id[:2]), exist_ok=True)

        with open(os.path.join(objects_path, commit_id[:2], commit_id[2:]), 'w') as commit:
            commit.write(f"User: {self.username}\n")
            commit.write(f"Date: {datetime.now()}\n")
            commit.write(f"Description: {description}\n")

            tree_hash = Utils.create_tree(self.repo_path)

            if self.__is_high_difference(tree_hash):
                commit.write(f"Type: diff\n")
            else:
                commit.write(f"Type: full\n")

            if self.last_commit_id is not None:
                commit.write(f"Tree: {tree_hash}\n")
                commit.write(f"Parent: {self.last_commit_id}\n")

            self.last_commit_id = commit_id

        if os.path.isfile(index_path):
            os.remove(index_path)

        self.__update_head()

    def branch(self, name):
        branch_path = os.path.join(self.repo_path, 'Refs', 'heads', name)

        if os.path.exists(branch_path):
            raise BranchAlreadyExitsError

        with open(branch_path, 'w') as branch:
            branch.write(self.last_commit_id)

    def checkout(self):
        pass #TODO

    def log(self):
        pass #TODO

    def __update_head(self):
        with open(os.path.join(self.repo_path, 'HEAD'), 'w') as head:
            head.write(f'ref: {self.last_commit_id}\n')

    def __create_directories(self):
        os.makedirs(self.repo_path, exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'Objects'), exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'Refs'), exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'Refs', 'heads'), exist_ok=True)

    def __is_high_difference(self, tree_hash):
        pass

    @staticmethod
    def __get_last_commit_id(path):
        head_path = os.path.join(path, 'HEAD')

        if not os.path.exists(head_path):
            return None

        with open(head_path, 'r') as head_file:
            ref = head_file.readline().strip().split(': ')[1]

        ref_path = os.path.join(path, ref)

        if os.path.exists(ref_path):
            with open(ref_path, 'r') as ref_file:
                return ref_file.readline().strip()

        return None

    @staticmethod
    def __get_seed(path):
        seed_path = os.path.join(path, 'SEED')

        if not os.path.exists(seed_path):
            return None

        with open(seed_path, 'r') as head_file:
            return int(head_file.readline().strip().split(': ')[1])
