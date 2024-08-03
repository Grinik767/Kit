#!/usr/bin/env python

import click
import os
from version_control import VersionControl


@click.group()
@click.pass_context
def main(ctx):
    """Kit Version Control System"""
    ctx.ensure_object(dict)
    repo_path = os.path.abspath('.')
    username = os.getenv('KIT_USERNAME', 'default_user')
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
@click.argument('name')
@click.option('-d', '--delete', is_flag=True, help="Delete the specified branch")
@click.pass_context
def branch(ctx, name, delete):
    """Create or manage branches"""
    vcs = ctx.obj['vcs']
    if delete:
        vcs.remove_branch(name)
        click.echo(f'\tBranch with name {name} deleted.')
    else:
        vcs.create_branch(name)
        click.echo(f'\tBranch with name {name} created.')


@click.command()
@click.pass_context
def branches(ctx):
    """Get all branches"""
    vcs = ctx.obj['vcs']
    for info in vcs.branches_list():
        click.echo(f'\tName: {info}')


@click.command()
@click.argument('name')
@click.option('-d', '--delete', is_flag=True, help="Delete the specified branch")
@click.option('-m', '--message', required=False, help="Tag message")
@click.pass_context
def tag(ctx, name, delete, message):
    """Create or manage tags"""
    vcs = ctx.obj['vcs']
    if delete:
        vcs.remove_tag(name)
        click.echo(f'\tTag with name {name} deleted.')
    else:
        vcs.create_tag(name, message)
        click.echo(f'\tTag with name {name} created.')


@click.command()
@click.pass_context
def tags(ctx):
    """Get all tags"""
    vcs = ctx.obj['vcs']
    for info in vcs.tags_list():
        info = info.split('\n')
        click.echo(f'\tName: {info[0]}; User: {info[1]}; Date: {info[2]}; Message: {info[3]}')


@click.command()
@click.argument('name')
@click.option('-b', '--branch', is_flag=True, help="Switch to the specified branch")
@click.option('-t', '--tag', is_flag=True, help="Switch to the specified tag")
@click.option('-c', '--commit', is_flag=True, help="Switch to the specified commit")
@click.pass_context
def checkout(ctx, name, branch, tag, commit):
    """Checkout to branch, commit or tag"""
    vcs = ctx.obj['vcs']

    if branch:
        vcs.checkout_to_branch(name)
    elif tag:
        vcs.checkout_to_tag(name)
    elif commit:
        vcs.checkout_to_commit(name)
    else:
        vcs.checkout(name)

    click.echo(f'\tChecked out to {name}')


@click.command()
@click.pass_context
def index(ctx):
    """Show index"""
    vcs = ctx.obj['vcs']
    for info in vcs.index():
        info = info.split(',')
        click.echo(f'\t{3 * info[2]} {info[0]}')


@click.command()
@click.pass_context
def log(ctx):
    """Show commit logs"""
    vcs = ctx.obj['vcs']
    for data in vcs.log():
        click.echo(f'\tCommit: {data[0]}; User: {data[1]}; Date: {data[2]}; Message: {data[3]}')


main.add_command(init)
main.add_command(add)
main.add_command(remove)
main.add_command(commit)
main.add_command(branch)
main.add_command(branches)
main.add_command(tag)
main.add_command(tags)
main.add_command(checkout)
main.add_command(index)
main.add_command(log)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        click.echo(f'\t{e}')
