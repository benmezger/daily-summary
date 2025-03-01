#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-03-01 Sat 20:36>


import sys
from collections import defaultdict
from datetime import date, datetime
from os import getenv
from typing import NamedTuple, TextIO

import click

from ._github import Github
from ._ollama import Ollama
from ._summary import Summary, write_summary


class _Context(NamedTuple):
    github: Github
    username: str


@click.group()
@click.option("--token", default=getenv("GITHUB_TOKEN", ""), type=str, required=True)
@click.option("--username", type=str, default="benmezger", show_default=True)
@click.pass_context
def cli(ctx: click.Context, token: str, username: str) -> None:
    ctx.obj = _Context(github=Github(token, username=username), username=username)


@cli.command()
@click.pass_context
@click.option(
    "--date",
    type=click.DateTime(formats=("%Y-%m-%d",)),
    required=True,
    default=datetime.now().date().strftime("%Y-%m-%d"),
    show_default=True,
)
@click.option(
    "--file",
    help="File to store output. Defaults to stdout",
    type=click.File("w"),
    default=sys.stdout,
)
def list_issues(ctx: click.Context, date: date, file: TextIO) -> None:
    context: _Context = ctx.obj
    file.writelines([f"{issue}\n" for issue in context.github.issues_from(date)])

    file.close()


@cli.command()
@click.option(
    "--file",
    help="File to store output. Defaults to stdout",
    type=click.File("w"),
    default=sys.stdout,
)
@click.pass_context
def account(ctx: click.Context, file: TextIO) -> None:
    context: _Context = ctx.obj
    acc = context.github.get_user()
    file.write(f"{acc}\n")
    file.close()


@cli.command()
@click.option(
    "--date",
    type=click.DateTime(formats=("%Y-%m-%d",)),
    required=True,
    default=datetime.now().date().strftime("%Y-%m-%d"),
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
    "--file",
    help="File to store output. Defaults to stdout",
    type=click.File("w"),
    default=sys.stdout,
)
@click.pass_context
def daily_summary(
    ctx: click.Context, date: date, ollama_model: str, ollama: bool, file: TextIO
) -> None:
    context: _Context = ctx.obj

    repository_summaries = defaultdict(list[Summary])
    for issue in list(context.github.issues_from(date)):
        repository_summaries[issue.repository].append(
            Summary(
                summary=(
                    issue.summarize(ollama=Ollama(ollama_model))
                    if ollama
                    else issue.title
                ).strip(),
                url=issue.url.strip(),
                is_pr=issue.is_pr,
                organization=issue.organization,
            )
        )

    write_summary(repository_summaries, file)
    file.close()
