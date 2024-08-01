class AlreadyExistError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'AlreadyExistError: {self.message}'
        else:
            return f'AlreadyExistError'


class CheckoutError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'CheckoutError: {self.message}'
        else:
            return f'CheckoutError'


class NothingToCommitError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'NothingToCommitError: {self.message}'
        else:
            return f'NothingToCommitError'


class NotOnBranchError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'NotOnBranchError: {self.message}'
        else:
            return f'NotOnBranchError'


class UncommitedChangesError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return f'UncommitedChangesError: {self.message}'
        else:
            return f'UncommitedChangesError'
