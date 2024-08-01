import errors
from os import path
from drive_manager import DriveManager
from utils import Utils
from random import randint
from datetime import datetime


class VersionControl:
    def __init__(self, username: str, workspace_path: str) -> None:
        self.username = username
        self.workspace_path = workspace_path
        self.repo_path = path.abspath(path.join(workspace_path, ".kit"))

        self.drive = DriveManager(self.workspace_path)
        self.head = self.drive.get_head()
        self.seed = self.drive.get_seed()
        self.current_id = self.drive.get_last_commit_id(self.head)

    def init(self) -> None:
        if self.drive.is_exist('.kit'):
            raise errors.AlreadyExistError.AlreadyExistError(f'This directory already have repository')

        self.head = path.join('Refs', 'heads', 'main')
        self.seed = randint(10 ** 7, 10 ** 8 - 1)

        self.drive.initialize_directories()
        self.commit("initial commit")

        self.drive.write(path.join('.kit', 'HEAD'), self.head)
        self.drive.write(path.join('.kit', 'SEED'), str(self.seed))
        self.drive.write(path.join('.kit', self.head), self.current_id)

    def add(self, local_path: str) -> None:
        self.drive.write_index_data(local_path, self.seed)

    def remove(self, local_path: str) -> None:
        index_path = path.join('.kit', 'INDEX')
        data = self.drive.read(index_path)
        new_data = []

        for line in data.split():
            file_path, hash = line.split()
            if file_path == local_path:
                continue

            new_data.append(f'{file_path} {hash}')

        self.drive.write(index_path, data.join('\n'))

    def commit(self, description: str) -> None:
        if self.head is None:
            raise errors.NotOnBranchError.NotOnBranchError

        index_path = path.join('.kit', 'INDEX')

        if self.current_id is not None and not self.drive.is_exist(index_path):
            raise errors.NothingToCommitError.NothingToCommitError

        commit_time = datetime.now()
        commit_id = Utils.get_string_hash(''.join((self.username, description, commit_time.isoformat())),
                                          seed=self.seed).hexdigest()
        tree_hash = Utils.get_tree_hash(self.repo_path, self.seed).hexdigest()

        self.drive.write_commit_data(commit_id, self.username, commit_time, description, tree_hash, self.current_id)

        if self.current_id is not None:
            self.drive.save_tree(tree_hash)

        self.drive.save_files_from_index()
        self.current_id = commit_id
        self.drive.write(path.join('.kit', self.head), self.current_id)

        if self.drive.is_exist(index_path):
            self.drive.remove(index_path)

    def branch(self, name: str) -> None:
        branch_path = path.join('.kit', 'Refs', 'heads', name)

        if self.drive.is_exist(branch_path):
            raise errors.AlreadyExistError.AlreadyExistError(f'Branch named {name} already exist')

        self.drive.write(branch_path, self.current_id)

    def tag(self, name: str, description: str = None) -> None:
        tag_path = path.join('.kit', 'Refs', 'tags', name)

        if self.drive.is_exist(tag_path):
            raise errors.AlreadyExistError.AlreadyExistError(f'Tag named {name} already exist')

        self.drive.write(tag_path, f"{self.username}\n{datetime.now()}\n{description}\n{self.current_id}")

    def checkout(self, name: str) -> None:
        tag_path = path.join('.kit', 'Refs', 'tags', name)
        branch_path = path.join('.kit', 'Refs', 'heads', name)
        index_path = path.join('.kit', 'INDEX')

        if self.drive.is_exist(tag_path):
            commit_id = self.drive.read(path.join('.kit', 'Refs', 'tags', name))
            self.drive.write(path.join('.kit', 'HEAD'), 'None')

        elif self.drive.is_exist(branch_path):
            commit_id = self.drive.read(branch_path)
            self.drive.write(path.join('.kit', 'HEAD'), branch_path)
        else:
            commit_id = name

        if self.drive.is_exist(index_path):
            raise errors.UncommitedChangesError.UncommitedChangesError

        self.head = self.drive.get_head()
        folder = commit_id[:2]
        filename = commit_id[2:]
        tree_id = self.drive.read(path.join('.kit', 'Objects', folder, filename)).split()[3]

        #TODO Вызов отгрузки

    def log(self) -> None:
        pass #TODO
