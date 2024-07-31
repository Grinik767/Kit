from utils import *


class Obj(ABC):

    def __init__(self, local_path: str, is_diff: bool):
        self._hash = None
        self._local_path = local_path
        self._is_diff = is_diff

    @property
    def hash(self) -> str:
        if self._hash is None:
            self._hash = self.get_hash()
        return self._hash

    @property
    def local_path(self) -> str:
        return self._local_path

    @property
    def is_diff(self) -> bool:
        return self._is_diff

    @abstractmethod
    def get_hash(self) -> str:
        pass
