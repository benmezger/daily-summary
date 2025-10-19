#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-03-01 Sat 20:36>


import sys
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import wraps
from itertools import chain
from os import getenv
from typing import Any, NamedTuple, TextIO

import click

from ._summary import maybe_write_github_summaries, maybe_write_header, maybe_write_misc
from .github import Github
from .models import GithubEvent, RepositoryEvents
from .ollama import Ollama


class _Context(NamedTuple):
    github: Github
    file: TextIO


def date_option(f: Callable[..., Any]) -> Callable[..., Any]:
    @click.option(
        "-d",
        "--date",
        type=click.DateTime(formats=("%Y-%m-%d", "%d-%m-%Y")),
        required=True,
        default=datetime.now().date().strftime("%d-%m-%Y"),
        show_default=True,
    )
    @wraps(f)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return f(*args, **kwargs)

    return wrapper


@click.group()
@click.option(
    "-t",
    "--token",
    default=getenv("GITHUB_TOKEN", ""),
    type=str,
    required=True,
)
@click.option(
    "-u",
    "--username",
    type=str,
    default=getenv("GITHUB_USERNAME", "benmezger"),
    show_default=True,
)
@click.option(
    "-f",
    "--file",
    help="File to store output. Defaults to stdout",
    type=click.File("w"),
    default=sys.stdout,
)
@click.pass_context
def cli(ctx: click.Context, token: str, username: str, file: TextIO) -> None:
    ctx.obj = _Context(github=Github(token, username=username), file=file)


@cli.command()
@date_option
@click.pass_context
def list_issues(ctx: click.Context, date: datetime) -> None:
    context: _Context = ctx.obj
    context.file.writelines(
        [f"{event}\n" for event in context.github.issues_from(date)]
    )


@cli.command()
@date_option
@click.pass_context
def list_commits(ctx: click.Context, date: datetime) -> None:
    context: _Context = ctx.obj
    context.file.writelines(
        [f"{event}\n" for event in context.github.commits_from(date)]
    )


@cli.command()
@click.pass_context
def account(ctx: click.Context) -> None:
    context: _Context = ctx.obj
    acc = context.github.get_user()
    context.file.write(f"{acc}\n")


@cli.command()
@date_option
@click.pass_context
def list_tags(ctx: click.Context, date: datetime) -> None:
    context: _Context = ctx.obj
    context.file.writelines([f"{event}\n" for event in context.github.tags_from(date)])


@cli.command()
@date_option
@click.pass_context
def list_comments(ctx: click.Context, date: datetime) -> None:
    context: _Context = ctx.obj
    context.file.writelines(
        [f"{event}\n" for event in context.github.comments_from(date)]
    )


@cli.command()
@date_option
@click.option(
    "--ollama-model",
    type=str,
    required=True,
    show_default=True,
    default="mistral",
)
@click.option(
    "--ollama/--no-ollama",
    is_flag=True,
    default=True,
    show_default=True,
    help="Enable/Disable Ollama summary generation",
)
@click.option(
    "-y",
    "--yesterday",
    is_flag=True,
    show_default=True,
    help="Create daily summary for yesterday",
)
@click.option(
    "--escape",
    is_flag=True,
    show_default=True,
    help="Escape backticks. Needed for posting summary as a Github issue",
)
@click.option(
    "--ollama-url",
    default="http://localhost:11434",
    type=str,
    show_default=True,
    help="Use custom Ollama URL.",
)
@click.pass_context
def daily_summary(
    ctx: click.Context,
    date: datetime,
    ollama_model: str,
    ollama: bool,
    yesterday: bool,
    escape: bool,
    ollama_url: str,
) -> None:
    context: _Context = ctx.obj

    repository_events: dict[str, list[GithubEvent]] = defaultdict(list)

    filter_date = (datetime.now() - timedelta(days=1)) if yesterday else date

    for event in chain(
        context.github.issues_from(filter_date),
        context.github.commits_from(filter_date),
        context.github.reviews_from(filter_date),
        context.github.tags_from(filter_date),
        context.github.comments_from(filter_date),
    ):
        repository_events[str(event.repository)].append(event)

    events = [
        RepositoryEvents(
            repository=evts[0].repository.name,
            organization=evts[0].repository.owner,
            events=evts,
        )
        for evts in repository_events.values()
    ]

    ollama_handler = Ollama(host=ollama_url, model=ollama_model) if ollama else None
    account = context.github.get_user()

    maybe_write_header(account, events, context.file, filter_date, escape)
    maybe_write_github_summaries(events, ollama_handler, context.file, escape)
    maybe_write_misc(events, context.file)
