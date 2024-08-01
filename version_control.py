from os import path
from drive_manager import DriveManager
from errors.NothingToCommitError import NothingToCommitError
from errors.RepositoryAlreadyExistError import RepositoryAlreadyExistError
from errors.BranchAlreadyExistError import BranchAlreadyExitsError
from utils import Utils
from xxhash import xxh3_128
from random import randint
from datetime import datetime


class VersionControl:
    def __init__(self, username, workspace_path):
        self.username = username
        self.workspace_path = workspace_path
        self.repo_path = path.abspath(path.join(workspace_path, ".kit"))

        self.drive = DriveManager(self.workspace_path)
        self.head = self.drive.get_head()
        self.seed = self.drive.get_seed()
        self.current_id = self.drive.get_last_commit_id(self.head)

    def init(self):
        if self.drive.is_exist('.kit'):
            raise RepositoryAlreadyExistError

        self.head = path.join('Refs', 'heads', 'main')
        self.seed = randint(10 ** 7, 10 ** 8 - 1)

        self.drive.initialize_directories()
        self.commit("initial commit")

        self.drive.write(path.join('.kit', 'HEAD'), self.head)
        self.drive.write(path.join('.kit', 'SEED'), str(self.seed))
        self.drive.write(path.join('.kit', self.head), self.current_id)

    def add(self, local_path: str):
        self.drive.write_index_data(local_path, self.seed)

    def commit(self, description: str):
        index_path = path.join('.kit', 'INDEX')

        if self.current_id is not None and not self.drive.is_exist(index_path):
            raise NothingToCommitError

        commit_id = xxh3_128(self.username + description + datetime.now().isoformat(), seed=self.seed).hexdigest()
        tree_hash = Utils.get_tree_hash(self.repo_path, self.seed)

        self.drive.write_commit_data(commit_id, self.username, datetime.now(), description, tree_hash.hexdigest(),
                                     self.current_id)

        if self.current_id is not None:
            self.drive.save_tree(tree_hash.hexdigest())

        self.drive.save_files_from_index()
        self.current_id = commit_id
        self.drive.write(path.join('.kit', self.head), self.current_id)

        if self.drive.is_exist(index_path):
            self.drive.remove(index_path)

    def branch(self, name):
        branch_path = path.join('.kit', 'Refs', 'heads', name)

        if self.drive.is_exist(branch_path):
            raise BranchAlreadyExitsError

        self.drive.write(branch_path, self.current_id)

    def checkout(self):
        pass  # TODO

    def log(self):
        pass  # TODO
