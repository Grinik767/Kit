#!/usr/bin/env python

import click
from os import path
from getpass import getuser
from version_control import VersionControl


@click.group()
@click.pass_context
def main(ctx):
    """Kit Version Control System"""
    ctx.ensure_object(dict)
    repo_path = path.abspath('.')
    username = getuser()
    ctx.obj['vcs'] = VersionControl(username, repo_path)


@click.command()
@click.pass_context
def init(ctx):
    """Initialize a new repository"""
    vcs = ctx.obj['vcs']
    vcs.init()
    click.echo(f"\tInitialized empty kit repository in {vcs.repo_path}")


@click.command()
@click.argument('file')
@click.pass_context
def add(ctx, file):
    """Add file contents to the index"""
    vcs = ctx.obj['vcs']
    vcs.add(file)
    click.echo(f"\tAdded {file} to index.")


@click.command()
@click.argument('file', required=False)
@click.pass_context
def remove(ctx, file):
    """Remove file contents from the index or repository"""
    vcs = ctx.obj['vcs']
    vcs.rm(file)
    click.echo(f"\tRemoved {file}.")


@click.command()
@click.option('-m', '--message', required=True, help="Commit message")
@click.pass_context
def commit(ctx, message):
    """Record changes to the repository"""
    vcs = ctx.obj['vcs']
    vcs.commit(message)
    click.echo(f"\tCommitted with message: {message}")


@click.command()
@click.argument('name', required=False)
@click.option('-a', '--all', is_flag=True, help="Show all branches")
@click.option('-b', '--branch', is_flag=True, help="Checkout to branch after creating")
@click.option('-d', '--delete', is_flag=True, help="Delete the specified branch")
@click.option('--show-current', is_flag=True, help="Show current branch")
@click.pass_context
def branch(ctx, name, all, branch, delete, show_current):
    """Create or manage branches"""
    vcs = ctx.obj['vcs']

    if all:
        for info in vcs.branches_list():
            click.echo(f'\tName: {info}')
        return

    if show_current:
        click.echo(f'\tCurrent branch: {vcs.current_branch()}')
        return

    if not name:
        raise click.UsageError("The [NAME] argument is required when using this option.")

    if delete:
        vcs.remove_branch(name)
        click.echo(f'\tBranch with name {name} deleted.')
        return

    vcs.create_branch(name)
    click.echo(f'\tBranch with name {name} created.')

    if branch:
        vcs.checkout_to_branch(name, True)
        click.echo(f'\tChecked out to {name}.')


@click.command()
@click.argument('name', required=False)
@click.option('-a', '--all', is_flag=True, help="Show all tags")
@click.option('-d', '--delete', is_flag=True, help="Delete the specified tag")
@click.option('-m', '--message', required=False, help="Tag message")
@click.pass_context
def tag(ctx, name, all, delete, message):
    """Create or manage tags"""
    vcs = ctx.obj['vcs']

    if all:
        for info in vcs.tags_list():
            info = info.split('\n')
            click.echo(f'\tName: {info[0]}; User: {info[1]}; Date: {info[2]}; Message: {info[3]}')
        return

    if not name:
        raise click.UsageError("The [NAME] argument is required when using this option.")

    if delete:
        vcs.remove_tag(name)
        click.echo(f'\tTag with name {name} deleted.')
    else:
        vcs.create_tag(name, message)
        click.echo(f'\tTag with name {name} created.')


@click.command()
@click.argument('name')
@click.option('-b', '--branch', is_flag=True, help="Switch to the specified branch")
@click.option('-t', '--tag', is_flag=True, help="Switch to the specified tag")
@click.option('-c', '--commit', is_flag=True, help="Switch to the specified commit")
@click.option('-f', '--force', is_flag=True, help="Force checkout")
@click.pass_context
def checkout(ctx, name, branch, tag, commit, force):
    """Checkout to branch, commit or tag"""
    vcs = ctx.obj['vcs']

    if branch:
        vcs.checkout_to_branch(name, force)
    elif tag:
        vcs.checkout_to_tag(name, force)
    elif commit:
        vcs.checkout_to_commit(name, force)
    else:
        vcs.checkout(name, force)

    click.echo(f'\tChecked out to {name}.')


@click.command()
@click.pass_context
def index(ctx):
    """Show index"""
    vcs = ctx.obj['vcs']
    for info in vcs.index():
        info = info.split(',')
        click.echo(f'\t{3 * info[2]} {info[0]}')


@click.command()
@click.option('-p', '--patch', is_flag=True, help="Show commits difference")
@click.option('-n', '--number', default=None, type=int, help="Number of commits to show")
@click.pass_context
def log(ctx, patch, number):
    """Show commit logs"""
    vcs = ctx.obj['vcs']

    commits = vcs.commits_list()
    previous_commit = next(commits)
    click.echo(f'\n\tCommit: {previous_commit[0]}; User: {previous_commit[1]}; Date: {previous_commit[2]}; '
               f''f'Message: 'f'{previous_commit[3]}')

    count = 1
    for current_commit in commits:
        if number is not None and count >= number:
            break

        if patch:
            for line in vcs.commits_diff(current_commit[0], previous_commit[0]):
                sign, file = line.split(';')
                click.echo(f'\t\t{3 * sign} {file}')

        click.echo(f'\n\tCommit: {current_commit[0]}; User: {current_commit[1]}; Date: {current_commit[2]}; '
                   f'Message: {current_commit[3]}')
        previous_commit = current_commit
        count += 1


main.add_command(init)
main.add_command(add)
main.add_command(remove)
main.add_command(commit)
main.add_command(branch)
main.add_command(tag)
main.add_command(checkout)
main.add_command(index)
main.add_command(log)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        click.echo(e)
