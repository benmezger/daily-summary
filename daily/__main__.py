from collections import defaultdict
from datetime import date, datetime
from os import getenv
import click

from daily.models import PR
from ._summary import summarize

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


@cli.command()
@click.pass_context
def account(ctx: click.Context) -> None:
    context: Context = ctx.obj
    acc = context.github.get_user()
    print(f"{acc.name} - @{acc.username}")


@cli.command()
@click.option(
    "--date",
    type=click.DateTime(formats=("%Y-%m-%d",)),
    required=True,
    default=datetime.now().date().strftime("%Y-%m-%d"),
)
@click.pass_context
def daily_summary(ctx: click.Context, date: date) -> None:
    context: Context = ctx.obj
    ordered_issues = defaultdict(list[PR])
    for issue in list(
        context.github.issues_from(date, organization=context.organization)
    ):
        ordered_issues[issue.repository].append(issue)

    for issues in ordered_issues.values():
        for summary in summarize(issues):
            print(summary)


if __name__ == "__main__":
    cli()
