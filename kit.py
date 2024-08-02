#!/usr/bin/env python

import argparse
import os
import errors
from version_control import VersionControl


def init(args, vcs):
    try:
        vcs.init()
        print(f"Initialized empty kit repository in {vcs.repo_path}")
    except errors.AlreadyExistError as e:
        print(e)


def add(args, vcs):
    try:
        vcs.add(args.file)
        print(f"Added {args.file} to index.")
    except FileNotFoundError:
        print(f"Error: File {args.file} not found.")


def remove(args, vcs):
    if args.file is None:
        vcs.remove()
        print(f"Removed all files from index.")
    else:
        try:
            vcs.remove(args.file)
            print(f"Removed {args.file} from index.")
        except FileNotFoundError:
            print(f"Error: File {args.file} not found.")


def commit(args, vcs):
    try:
        vcs.commit(args.message)
        print(f"Committed with message: {args.message}")
    except errors.NothingToCommitError as e:
        print(e)


def branch(args, vcs):
    try:
        vcs.branch(args.name)
        print(f'Branch with name {args.name} created.')
    except errors.AlreadyExistError as e:
        print(e)


def tag(args, vcs):
    try:
        vcs.tag(args.name, args.message)
        print(f'Tag with name {args.name} created.')
    except errors.AlreadyExistError as e:
        print(e)


def checkout(args, vcs):
    try:
        vcs.checkout(args.name)
        print(f'Checked out to {args.name}')
    except errors.CheckoutError as e:
        print(e)


def log(args, vcs):
    try:
        for data in vcs.log():
            print(f'Commit: {data[0]}; User: {data[1]}; Date: {data[2]}; Message: {data[3]}')
    except Exception as e:
        print(f"Error retrieving log: {e}")


def main():
    parser = argparse.ArgumentParser(description="Kit Version Control System")
    subparsers = parser.add_subparsers(dest="command", help="Sub-command help")

    init_parser = subparsers.add_parser("init", help="Initialize a new repository")
    init_parser.add_argument("path", nargs='?', default='.', help="Path to the working directory")
    init_parser.set_defaults(func=init)

    add_parser = subparsers.add_parser("add", help="Add file contents to the index")
    add_parser.add_argument("file", help="File or directory to add")
    add_parser.set_defaults(func=add)

    remove_parser = subparsers.add_parser("remove", help="Remove file contents from the index")
    remove_parser.add_argument("file", nargs='?', help="File or directory to remove")
    remove_parser.set_defaults(func=remove)

    commit_parser = subparsers.add_parser("commit", help="Record changes to the repository")
    commit_parser.add_argument("-m", "--message", required=True, help="Commit message")
    commit_parser.set_defaults(func=commit)

    branch_parser = subparsers.add_parser("branch", help="Create or manage branches")
    branch_parser.add_argument("name", help="Name of the new branch or branch to switch to")
    branch_parser.set_defaults(func=branch)

    tag_parser = subparsers.add_parser("tag", help="Create or manage tags")
    tag_parser.add_argument("name", help="Name of the new tag")
    tag_parser.add_argument("-m", "--message", required=True, help="Tag message")
    tag_parser.set_defaults(func=tag)

    checkout_parser = subparsers.add_parser("checkout", help="Checkout on branch/commit/tag")
    checkout_parser.add_argument("name", help="Name of the new branch or branch to switch to")
    checkout_parser.set_defaults(func=checkout)

    log_parser = subparsers.add_parser("log", help="Show commit logs")
    log_parser.set_defaults(func=log)

    args = parser.parse_args()
    repo_path = os.path.abspath(args.path if args.command == "init" else '.')
    vcs = VersionControl(os.getenv('KIT_USERNAME', 'default_user'), repo_path)

    if hasattr(args, 'func'):
        args.func(args, vcs)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
