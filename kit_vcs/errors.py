class BaseError(Exception):
    def __init__(self, *args):
        self.message = args[0] if args else None

    def __str__(self):
        if self.message:
            return f'{self.__class__.__name__}: {self.message}'
        return self.__class__.__name__


class AlreadyExistError(BaseError):
    pass


class CheckoutError(BaseError):
    pass


class NothingToCommitError(BaseError):
    pass


class NotOnBranchError(BaseError):
    pass


class UncommitedChangesError(BaseError):
    pass


class RepositoryExistError(BaseError):
    pass


class MergeConflictError(BaseError):
    pass
