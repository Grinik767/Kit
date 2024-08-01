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
    def __init__(self, workspace_path, username):
        self.path = workspace_path
        self.repo_path = os.path.abspath(os.path.join(workspace_path, ".kit"))
        self.username = username
        self.drive = DriveManager(workspace_path)
        self.head = self.__get_head()
        self.seed = self.__get_seed()
        self.current_id = self.__get_current_id()

    def init(self):
        if os.path.exists(self.repo_path):
            raise RepositoryAlreadyExistError

        self.head = os.path.join('Refs', 'heads', 'main')
        self.seed = randint(10000000, 99999999)
        self.__create_directories()
        open(os.path.join(self.repo_path, 'INDEX'), 'w').close()
        self.commit("initial commit")

        with open(os.path.join(self.repo_path, 'HEAD'), 'w') as head:
            head.write(self.head)

        with open(os.path.join(self.repo_path, 'SEED'), 'w') as seed:
            seed.write(f'{self.seed}')

        with open(os.path.join(self.repo_path, 'Refs', 'heads', 'main'), 'w') as main:
            main.write(f'{self.current_id}')

        self.__update_branch_head()

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
        index_path = os.path.join(self.path, 'INDEX')

        if self.current_id is not None and not os.path.exists(index_path):
            raise NothingToCommitError

        commit_time = datetime.now()
        commit_id = Utils.get_string_hash(''.join((self.username, description, commit_time.isoformat())),
                                          self.seed).hexdigest()
        os.makedirs(os.path.join(self.repo_path, 'Objects', commit_id[:2]), exist_ok=True)
        tree_hash = Utils.get_tree_hash(self.repo_path, self.seed).hexdigest()

        with open(os.path.join(self.repo_path, 'Objects', commit_id[:2], commit_id[2:]), 'w') as commit:
            commit.write(f"{self.username}\n")
            commit.write(f"{commit_time}\n")
            commit.write(f"{description}\n")
            commit.write(f"{tree_hash}\n")
            commit.write(f"{self.current_id}")

            self.current_id = commit_id
            self.__update_branch_head()

        with open(index_path, 'r') as index:
            for line in index.readlines():
                path, hash = line.rstrip().split()
                self.drive.save_file(path, hash)

        if self.current_id is not None:
            self.drive.save_tree(tree_hash)

        if os.path.exists(index_path):
            os.remove(index_path)

    def branch(self, name):
        branch_path = os.path.join(self.repo_path, 'Refs', 'heads', name)

        if os.path.exists(branch_path):
            raise BranchAlreadyExitsError

        with open(branch_path, 'w') as branch:
            branch.write(self.current_id)

    def checkout(self):
        pass  # TODO

    def log(self):
        pass  # TODO

    def __update_branch_head(self):
        with open(os.path.join(self.repo_path, self.head), 'w') as branch:
            branch.write(f'{self.current_id}')

    def __create_directories(self):
        os.makedirs(self.repo_path, exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'Objects'), exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'Refs'), exist_ok=True)
        os.makedirs(os.path.join(self.repo_path, 'Refs', 'heads'), exist_ok=True)

    def __get_current_tree_hash(self):
        folder = self.current_id[:2]
        name = self.current_id[2:]

        with open(os.path.join(self.repo_path, 'Objects', folder, name), 'r') as commit:
            return commit.readlines()[3].rstrip()

    def __get_head(self):
        head_path = os.path.join(self.repo_path, 'HEAD')

        if not os.path.exists(head_path):
            return None

        with open(head_path, 'r') as head_file:
            return head_file.readline()

    def __get_seed(self):
        seed_path = os.path.join(self.repo_path, 'SEED')

        if not os.path.exists(seed_path):
            return None

        with open(seed_path, 'r') as head_file:
            return int(head_file.read())

    def __get_current_id(self):
        if self.head is None:
            return None

        with open(os.path.join(self.repo_path, 'HEAD'), 'r') as head:
            branch_path = head.readline()

        with open(os.path.join(self.repo_path, branch_path), 'r') as branch_path:
            return branch_path.readline().rstrip()
