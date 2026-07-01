"""Bonsai CLI -- tools for the Obsidian vault."""

import click

from .digest import digest
from .fetch import fetch
from .lint import lint
from .mailbox import mailbox
from .search import search
from .zk import zk


@click.group()
def cli():
    """Bonsai -- tools for the Obsidian vault."""


cli.add_command(digest)
cli.add_command(search)
cli.add_command(fetch)
cli.add_command(lint)
cli.add_command(mailbox)
cli.add_command(zk)
