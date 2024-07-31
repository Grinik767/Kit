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
        self.head = VersionControl.__get_head(self.repo_path)
        self.seed = VersionControl.__get_seed(self.repo_path)

    def init(self):
        if os.path.exists(self.repo_path):
            raise RepositoryAlreadyExistError

        self.head = None
        self.seed = randint(10000000, 99999999)
        self.__create_directories()
        self.commit("initial commit")

        with open(os.path.join(self.repo_path, 'SEED'), 'w') as seed:
            seed.write(f'{self.seed}\n')

        with open(os.path.join(self.repo_path, 'Refs', 'heads', 'main'), 'w') as main:
            main.write(f'{self.head}\n')

        self.__update_head()

    def add(self, local_path: str):
        index_path = os.path.join(self.repo_path, 'INDEX')
        file_path = os.path.join(self.path, local_path)

        with open(index_path, 'a') as index:
            if not os.path.isdir(file_path):
                index.write(f"{local_path} {Utils.get_file_hash(file_path, xxh3_128(seed=self.seed)).hexdigest()}\n")
                return

            for root, _, files in os.walk(file_path):
                for file in files:
                    file_full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_full_path, start=self.path)
                    self.add(relative_path)

    def commit(self, description: str):
        tree_hash = 1#Utils.get_tree_hash(self.repo_path)

        if self.head is not None and tree_hash == self.__get_head_tree_hash():
            raise NothingToCommitError

        commit_id = xxh3_128(self.username + description + datetime.now().isoformat(), seed=self.seed).hexdigest()
        os.makedirs(os.path.join(self.repo_path, 'Objects', commit_id[:2]), exist_ok=True)

        with open(os.path.join(self.repo_path, 'Objects', commit_id[:2], commit_id[2:]), 'w') as commit:
            commit.write(f"{self.username}\n")
            commit.write(f"{datetime.now()}\n")
            commit.write(f"{description}\n")
            commit.write(f"{tree_hash}\n")
            commit.write(f"{self.head}\n")

            self.head = commit_id

        self.__update_head()

    def branch(self, name):
        branch_path = os.path.join(self.repo_path, 'Refs', 'heads', name)

        if os.path.exists(branch_path):
            raise BranchAlreadyExitsError

        with open(branch_path, 'w') as branch:
            branch.write(self.head)

    def checkout(self):
        pass #TODO

    def log(self):
        pass #TODO

    def __update_head(self):
        with open(os.path.join(self.repo_path, 'HEAD'), 'w') as head:
            head.write(f'{self.head}\n')

    def __create_directories(self):
        os.makedirs(self.repo_path, exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'Objects'), exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'Refs'), exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'Refs', 'heads'), exist_ok=True)

    def __get_head_tree_hash(self):
        folder = self.head[:2]
        name = self.head[2:]

        with open(os.path.join(self.repo_path, 'Objects', folder, name), 'r') as head:
            return head[3]

    @staticmethod
    def __get_head(path):
        head_path = os.path.join(path, 'HEAD')

        if not os.path.exists(head_path):
            return None

        with open(head_path, 'r') as head_file:
            ref = head_file.readline()

        ref_path = os.path.join(path, ref)

        if os.path.exists(ref_path):
            with open(ref_path, 'r') as ref_file:
                return ref_file.readline()

        return None

    @staticmethod
    def __get_seed(path):
        seed_path = os.path.join(path, 'SEED')

        if not os.path.exists(seed_path):
            return None

        with open(seed_path, 'r') as head_file:
            return int(head_file.readline())
