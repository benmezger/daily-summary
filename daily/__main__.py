from collections import defaultdict
from datetime import date, datetime
from os import getenv
from typing import TextIO
import click
import sys

from ._ollama import Ollama
from ._github import Github
from ._summary import write_summary, Summary


class Context:
    def __init__(self, github: Github, organization: str | None):
        self.github = github
        self.organization = organization


@click.group()
@click.option("--token", default=getenv("GITHUB_TOKEN", ""), type=str, required=True)
@click.option("--organization", type=str)
@click.pass_context
def cli(ctx: click.Context, token: str, organization: str | None) -> None:
    ctx.obj = Context(github=Github(token), organization=organization)


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
    context: Context = ctx.obj
    for issue in context.github.issues_from(date, organization=context.organization):
        file.write(f"{issue}\n")

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
    context: Context = ctx.obj
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
    context: Context = ctx.obj

    repository_summaries = defaultdict(list[Summary])
    for issue in list(
        context.github.issues_from(date, organization=context.organization)
    ):
        repository_summaries[issue.repository].append(
            Summary(
                summary=(
                    issue.summarize(ollama=Ollama(ollama_model))
                    if ollama
                    else issue.title
                ).strip(),
                url=issue.url.strip(),
                is_pr=issue.is_pr,
            )
        )

    write_summary(repository_summaries, file)
    file.close()


if __name__ == "__main__":
    cli()
