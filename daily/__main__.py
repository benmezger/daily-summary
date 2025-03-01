from datetime import date, datetime
from os import getenv
import click

from ._github import Github


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
)
def list_prs(ctx: click.Context, date: date) -> None:
    context: Context = ctx.obj
    for issue in context.github.issues_from(date, organization=context.organization):
        print(issue)


if __name__ == "__main__":
    cli()
