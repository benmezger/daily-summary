#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-03-01 Sat 20:36>


import sys
from collections import defaultdict
from datetime import date, datetime
from os import getenv
from typing import NamedTuple, TextIO

import click

from daily.models import RepositoryEvents

from ._github import Github
from ._ollama import Ollama
from ._summary import (
    maybe_write_commit_summary,
    maybe_write_header,
    maybe_write_issue_summary,
    maybe_write_misc,
)


class _Context(NamedTuple):
    github: Github
    file: TextIO


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
    default="benmezger",
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
@click.option(
    "-d",
    "--date",
    type=click.DateTime(formats=("%Y-%m-%d", "%d-%m-%Y")),
    required=True,
    default=datetime.now().date().strftime("%d-%m-%Y"),
    show_default=True,
)
@click.pass_context
def list_issues(ctx: click.Context, date: date) -> None:
    context: _Context = ctx.obj
    context.file.writelines(
        [f"{event}\n" for event in context.github.issues_from(date)]
    )

    context.file.close()


@cli.command()
@click.option(
    "-d",
    "--date",
    type=click.DateTime(formats=("%Y-%m-%d", "%d-%m-%Y")),
    required=True,
    default=datetime.now().date().strftime("%d-%m-%Y"),
    show_default=True,
)
@click.pass_context
def list_commits(ctx: click.Context, date: date) -> None:
    context: _Context = ctx.obj
    context.file.writelines(
        [f"{event}\n" for event in context.github.commits_from(date)]
    )

    context.file.close()


@cli.command()
@click.pass_context
def account(ctx: click.Context) -> None:
    context: _Context = ctx.obj
    acc = context.github.get_user()
    context.file.write(f"{acc}\n")
    context.file.close()


@cli.command()
@click.option(
    "-d",
    "--date",
    type=click.DateTime(formats=("%Y-%m-%d", "%d-%m-%Y")),
    required=True,
    default=datetime.now().date().strftime("%d-%m-%Y"),
    show_default=True,
)
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
@click.pass_context
def daily_summary(
    ctx: click.Context, date: date, ollama_model: str, ollama: bool
) -> None:
    context: _Context = ctx.obj

    repository_events = defaultdict(list)

    for event in list(context.github.issues_from(date)) + list(
        context.github.commits_from(date)
    ):
        repository_events[event.repository].append(event)

    events = [
        RepositoryEvents(
            repository=repo, events=evts, organization=evts[0].organization
        )
        for repo, evts in repository_events.items()
    ]

    ollama_handler = Ollama(ollama_model) if ollama else None

    maybe_write_header(events, context.file)
    maybe_write_issue_summary(events, ollama_handler, context.file)
    maybe_write_commit_summary(events, context.file)
    maybe_write_misc(events, context.file)

    context.file.close()
