from drive_manager import DriveManager
from utils import *


class VersionControl:
    def __init__(self, username: str, workspace_path: str) -> None:
        self.username = username
        self.workspace_path = workspace_path
        self.repo_path = path.abspath(path.join(workspace_path, ".kit"))
        self.index_path = path.join('.kit', 'INDEX')

        self.drive = DriveManager(self.workspace_path)
        self.head = self.drive.get_head()
        self.seed = self.drive.get_seed()
        self.current_id = self.drive.get_last_commit_id(self.head)

    def init(self) -> None:
        if self.drive.is_exist('.kit'):
            raise errors.AlreadyExistError(f'This directory already have repository')

        self.head = path.join('refs', 'heads', 'main')
        self.seed = randint(10 ** 7, 10 ** 8 - 1)

        self.drive.initialize_directories()
        self.commit("initial commit")

        self.drive.write(path.join('.kit', 'HEAD'), self.head)
        self.drive.write(path.join('.kit', 'SEED'), str(self.seed))
        self.drive.write(path.join('.kit', self.head), self.current_id)

    @Utils.check_repository_exists
    def add(self, local_path: str) -> None:
        self.drive.calculate_index_data(local_path, self.drive.get_commit_tree_hash(self.current_id), self.seed)
        self.drive.write_index_data()
        self.drive.delete_if_empty_file(path.join('.kit', 'INDEX'))

    @Utils.check_repository_exists
    def rm(self, local_path: str) -> None:
        self.drive.calculate_index_data(local_path, self.drive.get_commit_tree_hash(self.current_id),
                                        self.seed, False)
        self.drive.write_index_data()
        self.drive.delete_if_empty_file(path.join('.kit', 'INDEX'))

    @Utils.check_repository_exists
    def index(self) -> str:
        if not self.drive.is_exist(self.index_path):
            return

        for line in self.drive.read(self.index_path).split('\n')[:-1]:
            yield line

    @Utils.check_repository_exists
    def commit(self, description: str) -> None:
        if self.current_id is not None and not self.drive.is_exist(self.index_path):
            raise errors.NothingToCommitError("No changes detected in the index. There is nothing to commit.")

        commit_time = datetime.now()
        commit_id = Utils.get_string_hash(''.join((self.username, description, commit_time.isoformat())),
                                          seed=self.seed).hexdigest()
        tree_hash = Utils.get_tree_hash(self.repo_path, self.seed).hexdigest()

        self.drive.write_commit_data(commit_id, self.username, commit_time, description, tree_hash, self.current_id)

        if self.current_id is not None:
            self.drive.save_tree(tree_hash, self.drive.get_commit_tree_hash(self.current_id))

        self.drive.rm_index_files()
        self.drive.save_files_from_index()
        self.current_id = commit_id

        if path.exists(path.join(self.repo_path, 'objects', self.head[:2], self.head[2:])):
            self.drive.write(path.join('.kit', 'HEAD'), self.current_id)
        else:
            self.drive.write(path.join('.kit', self.head), self.current_id)

        if self.drive.is_exist(self.index_path):
            self.drive.remove(self.index_path)
            self.drive.index_hashes.clear()

    @Utils.check_repository_exists
    def commits_list(self) -> (str, str, str, str):
        name = self.current_id

        while name != 'None':
            user, date, description, _, parent = self.drive.read(
                path.join('.kit', "objects", name[:2], name[2:])).split('\n')
            yield name, user, date, description
            name = parent

    @Utils.check_repository_exists
    def commits_diff(self, commit1_hash: str, commit2_hash: str) -> (str, str, str):
        tree1_hash = self.drive.commit_to_tree(commit1_hash)
        tree2_hash = self.drive.commit_to_tree(commit2_hash)
        tree1_path = path.abspath(path.join('.kit', "objects", tree1_hash[:2], tree1_hash[2:]))
        tree2_path = path.abspath(path.join('.kit', "objects", tree2_hash[:2], tree2_hash[2:]))

        for line in Utils.get_tree_diff(tree1_path, tree2_path):
            yield line

    @Utils.check_repository_exists
    def create_branch(self, name: str) -> None:
        branch_path = path.join('.kit', 'refs', 'heads', name)

        if self.drive.is_exist(branch_path):
            raise errors.AlreadyExistError(f'Branch named {name} already exist')

        self.drive.write(branch_path, self.current_id)

    @Utils.check_repository_exists
    def branches_list(self) -> (str, str, str):
        branches_path = path.join('.kit', 'refs', 'heads')
        for branch in self.drive.get_files_in_dir(branches_path):
            yield branch

    @Utils.check_repository_exists
    def remove_branch(self, name: str) -> None:
        branch_path = path.join('.kit', 'refs', 'heads', name)
        current_branch = path.basename(self.head)

        if current_branch == name:
            self.drive.write(path.join('.kit', 'HEAD'), self.current_id)

        if self.drive.is_exist(branch_path):
            self.drive.remove(branch_path)

    @Utils.check_repository_exists
    def create_tag(self, name: str, description: str = None) -> None:
        tag_path = path.join('.kit', 'refs', 'tags', name)

        if self.drive.is_exist(tag_path):
            raise errors.AlreadyExistError(f'Tag named {name} already exist')

        self.drive.write(tag_path, f"{self.username}\n{datetime.now()}\n{description}\n{self.current_id}")

    @Utils.check_repository_exists
    def tags_list(self) -> (str, str, str):
        tags_path = path.join('.kit', 'refs', 'tags')
        for tag in self.drive.get_files_in_dir(tags_path):
            yield f'{tag}\n{self.drive.read(path.join(tags_path, tag))}'

    @Utils.check_repository_exists
    def remove_tag(self, name: str) -> None:
        tag_path = path.join('.kit', 'refs', 'tags', name)

        if self.drive.is_exist(tag_path):
            self.drive.remove(tag_path)

    @Utils.check_repository_exists
    def checkout_to_commit(self, name: str, force: bool) -> None:
        commit_path = path.join("objects", name[:2], name[2:])
        self.__check_checkout_possibility('Commit', force, commit_path, name)
        commit_id = name
        self.drive.write(path.join('.kit', 'HEAD'), commit_id)
        self.__load_commit_data(commit_id)

    @Utils.check_repository_exists
    def checkout_to_tag(self, name: str, force: bool) -> None:
        tag_path = path.join('refs', 'tags', name)
        self.__check_checkout_possibility('Tag', force, tag_path, name)
        commit_id = self.drive.read(path.join('.kit', tag_path)).split()[-1]
        self.drive.write(path.join('.kit', 'HEAD'), commit_id)
        self.__load_commit_data(commit_id)

    @Utils.check_repository_exists
    def checkout_to_branch(self, name: str, force: bool) -> None:
        branch_path = path.join('refs', 'heads', name)
        self.__check_checkout_possibility('Branch', force, branch_path, name)
        commit_id = self.drive.read(path.join('.kit', branch_path))
        self.drive.write(path.join('.kit', 'HEAD'), branch_path)
        self.__load_commit_data(commit_id)

    @Utils.check_repository_exists
    def checkout(self, name: str, force: bool) -> None:
        tag_path = path.join('refs', 'tags', name)
        branch_path = path.join('refs', 'heads', name)
        commit_path = path.join('.kit', "objects", name[:2], name[2:])

        if self.drive.is_exist(self.index_path) and not force:
            raise errors.UncommitedChangesError("You have uncommitted changes in your working directory. ""Please "
                                                "commit or discard them before switching branches, tags, or commits.")

        if self.drive.is_exist(path.join('.kit', branch_path)):
            self.checkout_to_branch(name, force)
        elif self.drive.is_exist(path.join('.kit', tag_path)):
            self.checkout_to_tag(name, force)
        elif self.drive.is_exist(commit_path):
            self.checkout_to_commit(name, force)
        else:
            raise errors.CheckoutError(f"Commit/branch/tag with name {name} does not exist")

    @Utils.check_repository_exists
    def current_branch(self) -> str:
        if self.drive.is_exist(path.join('.kit', "objects", self.head[:2], self.head[2:])):
            raise errors.NotOnBranchError("You are not on a branch")

        return path.basename(self.head)

    def __load_commit_data(self, commit_id: str) -> None:
        self.head = self.drive.get_head()
        self.drive.delete_tree_files(self.drive.get_commit_tree_hash(self.current_id))
        self.drive.load_tree_files(self.drive.get_commit_tree_hash(commit_id))
        self.current_id = commit_id

    def __check_checkout_possibility(self, checkout_type: str, force: bool, checkout_path, name) -> None:
        if self.drive.is_exist(self.index_path) and not force:
            raise errors.UncommitedChangesError("You have uncommitted changes in your working directory. ""Please "
                                                "commit or discard them before switching branches, tags, or commits.")

        if not self.drive.is_exist(path.join('.kit', checkout_path)):
            raise errors.CheckoutError(f"{checkout_type} with name {name} does not exist")


if __name__ == '__main__':
    pass
