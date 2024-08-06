from utils import *


class DriveManager:
    def __init__(self, workspace_path: str) -> None:
        self.workspace_path = workspace_path
        self.repo_path = path.join(self.workspace_path, '.kit')
        self.index_path = path.join(self.repo_path, 'INDEX')
        self.index_hashes = self.get_index_hashes()

    def save_file(self, local_path: str, file_hash: str) -> None:
        folder = file_hash[:2]
        name = file_hash[2:]

        input_path = path.join(self.workspace_path, local_path)
        output_folder = path.join(self.repo_path, 'objects', folder)
        output_path = path.join(output_folder, name)

        makedirs(output_folder, exist_ok=True)

        with open(input_path, 'rb') as input_file, lzma.open(output_path, 'wb') as output_file:
            for chunk in iter(lambda: input_file.read(4096), b""):
                output_file.write(chunk)

    def save_tree(self, tree_hash: str, prev_tree_hash: str) -> None:
        prev_tree_path = path.join(self.repo_path, 'objects', prev_tree_hash[:2], prev_tree_hash[2:])
        hash_folder = path.join(self.repo_path, 'objects', tree_hash[:2], tree_hash[2:])
        makedirs(hash_folder, exist_ok=True)
        if path.exists(prev_tree_path):
            copy_tree(prev_tree_path, hash_folder)

        for filepath in self.index_hashes:
            file_hash, is_add = self.index_hashes[filepath][0], self.index_hashes[filepath][1]
            folder_name = path.split(filepath)[:-1][0]
            folder_path = path.join(hash_folder, folder_name)
            if folder_name:
                makedirs(folder_path, exist_ok=True)
            filepath = path.join(folder_path, path.basename(filepath))

            if is_add:
                with open(filepath, 'w') as f:
                    f.write(file_hash)
                continue
            remove(filepath)

    def load_file(self, file_hash: str, output_path: str) -> None:
        folder = file_hash[:2]
        name = file_hash[2:]
        compressed_path = path.join(self.repo_path, 'objects', folder, name)

        makedirs(path.dirname(output_path), exist_ok=True)

        with lzma.open(compressed_path, 'rb') as compressed_file, open(output_path, 'wb') as output_file:
            for chunk in iter(lambda: compressed_file.read(4096), b""):
                output_file.write(chunk)

    def save_files_from_index(self) -> None:
        for filepath in self.index_hashes:
            if self.index_hashes[filepath][1]:
                self.save_file(filepath, self.index_hashes[filepath][0])

    def write(self, local_path: str, data: str) -> None:
        with open(path.join(self.workspace_path, local_path), 'w') as file:
            file.write(data)

    def read(self, local_path: str) -> str:
        with open(path.join(self.workspace_path, local_path), 'r') as file:
            return file.read()

    def write_commit_data(self, commit_id: str, username: str, commit_dt: str | datetime, description: str, tree: str,
                          parent: str | None) -> None:
        makedirs(path.join(self.repo_path, 'objects', commit_id[:2]), exist_ok=True)
        with open(path.join(self.repo_path, 'objects', commit_id[:2], commit_id[2:]), 'w') as commit:
            commit.write(f"{username}\n{commit_dt}\n{description}\n{tree}\n{parent}")

    def calculate_index_data(self, local_path: str, prev_tree_hash: str, seed: int, is_add: bool = True) -> None:
        file_path = path.join(self.workspace_path, local_path)
        if Utils.check_for_dot_path(file_path):
            return
        if not path.isdir(file_path):
            rel_path = path.relpath(file_path, start=self.workspace_path)
            filehash = Utils.get_file_hash(file_path, self.workspace_path, seed).hexdigest()

            prev_tree_path = path.join(self.repo_path, 'objects', prev_tree_hash[:2], prev_tree_hash[2:])
            prev_filehash = None
            if path.exists(path.join(prev_tree_path, rel_path)):
                with open(path.join(prev_tree_path, rel_path), 'r') as f:
                    prev_filehash = f.read().strip()

            if is_add:
                if prev_filehash is None or prev_filehash != filehash:
                    self.index_hashes[rel_path] = (filehash, True)
                elif prev_filehash == filehash and rel_path in self.index_hashes:
                    del self.index_hashes[rel_path]
            elif not is_add and prev_filehash is not None:
                self.index_hashes[rel_path] = (filehash, False)
            elif not is_add and prev_filehash is None:
                del self.index_hashes[rel_path]
            return

        for root, _, files in walk(file_path):
            for file in files:
                file_full_path = path.join(root, file)
                relative_path = path.relpath(file_full_path, start=self.workspace_path)
                self.calculate_index_data(relative_path, prev_tree_hash, seed, is_add)

    def write_index_data(self) -> None:
        with open(self.index_path, 'w') as f:
            for filepath in self.index_hashes:
                f.write(
                    f"{filepath},{self.index_hashes[filepath][0]},"
                    f"{Utils.bool_to_sign(self.index_hashes[filepath][1])}\n"
                )

    def rm_index_files(self) -> None:
        for lcl_filepath in self.index_hashes:
            if not self.index_hashes[lcl_filepath][1]:
                filepath = path.join(self.workspace_path, lcl_filepath)
                if path.exists(filepath):
                    remove(filepath)

    def load_tree_files(self, tree_hash: str) -> None:
        if not tree_hash:
            return
        tree_path = path.join(self.repo_path, 'objects', tree_hash[:2], tree_hash[2:])

        for root, dirs, files in walk(tree_path):
            rel_path = path.relpath(root, start=tree_path)
            makedirs(rel_path, exist_ok=True)

            for file in files:
                with open(path.join(root, file), 'r') as f:
                    filehash = f.read().strip()
                self.load_file(filehash, path.join(self.workspace_path, rel_path, file))

    def delete_tree_files(self, tree_hash: str) -> None:
        if not tree_hash:
            return
        tree_path = path.join(self.repo_path, 'objects', tree_hash[:2], tree_hash[2:])

        for root, dirs, files in walk(tree_path, topdown=False):
            for file in files:
                full_path = path.join(self.workspace_path, path.relpath(path.join(root, file), start=tree_path))
                if path.exists(full_path):
                    remove(full_path)

            for directory in dirs:
                full_path = path.join(self.workspace_path, path.relpath(path.join(root, directory), start=tree_path))
                if path.exists(full_path):
                    rmdir(full_path)

    def get_index_hashes(self) -> dict[str: str]:
        result = {}
        if not path.exists(self.index_path):
            return result

        with open(self.index_path, 'r') as f:
            for line in f:
                filepath, filehash, diff_type = line.split(',')
                result[filepath] = (filehash, Utils.sign_to_bool(diff_type.strip()))
        return result

    def initialize_directories(self) -> None:
        makedirs(self.repo_path, exist_ok=True)
        makedirs(path.join(self.repo_path, 'objects'), exist_ok=True)
        makedirs(path.join(self.repo_path, 'refs'), exist_ok=True)
        makedirs(path.join(self.repo_path, 'refs', 'heads'), exist_ok=True)
        makedirs(path.join(self.repo_path, 'refs', 'tags'), exist_ok=True)

        open(path.join(self.repo_path, 'INDEX'), 'w').close()

        if platform.system() == "Windows":
            subprocess.run(['attrib', '+H', self.repo_path], check=True)

    def get_head(self) -> str | None:
        head_path = path.join(self.repo_path, 'HEAD')
        if not path.exists(head_path):
            return

        with open(head_path, 'r') as head_file:
            return head_file.readline()

    def get_seed(self) -> int | None:
        seed_path = path.join(self.repo_path, 'SEED')
        if not path.exists(seed_path):
            return

        with open(seed_path, 'r') as head_file:
            return int(head_file.read())

    def get_last_commit_id(self, head: str | None) -> str | None:
        if head is None:
            return

        if path.exists(path.join(self.repo_path, 'objects', head[:2], head[2:])):
            return head

        with open(path.join(self.repo_path, 'HEAD'), 'r') as head:
            branch_path = head.readline()

        with open(path.join(self.repo_path, branch_path), 'r') as branch:
            return branch.readline().rstrip()

    def get_commit_tree_hash(self, commit_id: str) -> str | None:
        commit_path = path.join(self.repo_path, 'objects', commit_id[:2], commit_id[2:])
        if not path.exists(commit_path):
            return

        with open(commit_path, 'r') as f:
            return f.readlines()[-2][:-1]

    def is_exist(self, local_path: str) -> bool:
        return path.exists(path.join(self.workspace_path, local_path))

    def delete_if_empty_file(self, local_path: str) -> None:
        full_path = path.join(self.workspace_path, local_path)
        if path.exists(full_path) and path.getsize(full_path) == 0:
            remove(full_path)

    def get_files_in_dir(self, local_path: str) -> str:
        full_path = path.join(self.workspace_path, local_path)
        for _, _, branches in walk(full_path):
            for branch in branches:
                yield branch

    def commit_to_tree(self, commit_hash: str) -> str:
        return self.read(path.join('.kit', "objects", commit_hash[:2], commit_hash[2:])).split('\n')[3]

    def remove(self, local_path: str) -> None:
        remove(path.join(self.workspace_path, local_path))


if __name__ == '__main__':
    pass
