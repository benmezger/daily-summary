from collections import defaultdict
from datetime import date, datetime
from os import getenv
import click

from daily.models import PR

from ._ollama import Ollama
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
@click.option(
    "--ollama-model",
    type=str,
    required=True,
    default="mistral",
)
@click.option(
    "--ollama/--no-ollama",
    is_flag=True,
    default=True,
    help="Enable/Disable Ollama summary generation",
)
@click.pass_context
def daily_summary(
    ctx: click.Context, date: date, ollama_model: str, ollama: bool
) -> None:
    context: Context = ctx.obj
    ordered_issues = defaultdict(list[PR])
    for issue in list(
        context.github.issues_from(date, organization=context.organization)
    ):
        ordered_issues[issue.repository].append(issue)

    print("Engineering")
    for repository, issues in ordered_issues.items():
        if not issues:
            continue

        print(f"* `{repository}`")
        for issue in issues:
            if ollama:
                print(
                    f"    ** {issue.summarize(ollama=Ollama(ollama_model))} "
                    f"[PR]({issue.url})"
                )
            else:
                print(f"    ** {issue.title} [PR]({issue.url})")

        print()

    print("Meetings")
    print("    * ")

    print("Misc")
    print("    * PR reviews and discussions")


if __name__ == "__main__":
    cli()
