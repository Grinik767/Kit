import os
import lzma


class DriveManager:
    def __init__(self, path):
        self.path = path
        self.repo_path = os.path.join(self.path, '.kit')

    def save(self, hash):
        folder = hash[:2]
        name = hash[2:]
        local_path = self.__get_original_file_location(hash)

        with open(os.path.join(self.path,local_path), 'rb') as file:
            data = bytes(file.read())
            compressed_data = lzma.compress(data)

        os.makedirs(os.path.join(self.repo_path, 'Objects', folder), exist_ok=True)

        with open(os.path.join(self.repo_path, 'Objects', folder, name), 'wb') as file:
            file.write(compressed_data)

    def load(self, hash):
        folder = hash[:2]
        name = hash[2:]

        with open(os.path.join(self.repo_path, 'Objects', folder, name), 'rb') as file:
            compressed_data = file.read()

        return lzma.decompress(compressed_data)

    def load_commmit(self, hash):
        folder = hash[:2]
        name = hash[2:]

        with open(os.path.join(self.repo_path, 'Objects', folder, name), 'rb') as commit:
            commit_data = commit.readlines()
            if len(commit_data) > 3:
                tree_hash = commit_data[3]
            else:
                tree_hash = None

    def __get_original_file_location(self, hash):
        with open(os.path.join(self.repo_path, 'INDEX'), 'r') as index:
            for file in index.readlines():
                file_path, file_hash = file.strip().split(', hash: ')
                file_path = file_path.split(': ')[1]
                file_hash = file_hash.strip()

                if file_hash == hash:
                    return file_path

        return None
