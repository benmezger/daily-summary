#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-03-01 Sat 20:36>


import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
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
    date: date,
    ollama_model: str,
    ollama: bool,
    yesterday: bool,
    escape: bool,
    ollama_url: str,
) -> None:
    context: _Context = ctx.obj

    repository_events = defaultdict(list)

    filter_date = date
    if yesterday:
        filter_date = (datetime.now() - timedelta(days=1)).date()

    for event in list(context.github.issues_from(filter_date)) + list(
        context.github.commits_from(filter_date)
    ):
        repository_events[event.repository].append(event)

    events = [
        RepositoryEvents(
            repository=repo, events=evts, organization=evts[0].organization
        )
        for repo, evts in repository_events.items()
    ]

    ollama_handler = Ollama(host=ollama_url, model=ollama_model) if ollama else None

    maybe_write_header(events, context.file, filter_date)
    maybe_write_issue_summary(events, ollama_handler, context.file, escape)
    maybe_write_commit_summary(events, ollama_handler, context.file, escape)
    maybe_write_misc(events, context.file)

    context.file.close()
