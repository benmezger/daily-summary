#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>

from collections.abc import AsyncIterator, Iterator
from datetime import datetime

from click.testing import CliRunner

from daily._cli import cli
from daily.github import Github
from daily.models import Account, EventType, GithubEvent, Repository


def test_pull_requests_from_uses_updated_date_query(monkeypatch):
    github = Github("token", username="benmezger")
    pull_request = GithubEvent(
        id="pr-123",
        title="Add missing PR summary",
        url="https://github.com/benmezger/daily-summary/pull/123",
        created_at=datetime(2026, 9, 11, 8, 0, 0),
        updated_at=datetime(2026, 9, 11, 12, 0, 0),
        repository=Repository(owner="benmezger", name="daily-summary"),
        event_type=EventType.PULL_REQUEST,
        state="MERGED",
    )
    query: dict[str, str] = {}

    def fake_make_graphql_request(self, graphql_query: str, path: str):
        query["graphql_query"] = graphql_query
        query["path"] = path
        return [pull_request]

    monkeypatch.setattr(Github, "_make_graphql_request", fake_make_graphql_request)

    result = list(github.pull_requests_from(datetime(2026, 9, 11), [], []))

    assert result == [pull_request]
    assert query == {
        "graphql_query": """
{
  search(
    query: "author:benmezger updated:2026-09-11 is:pr"
    type: ISSUE
    first: 100
  ) {
    edges {
      node {
        ... on PullRequest {
          id
          title
          body
          url
          repository {
            nameWithOwner
          }
          createdAt
          updatedAt
          state
          mergedAt
        }
      }
    }
  }
}
""",
        "path": "data.search.edges",
    }


def test_daily_summary_includes_authored_pull_requests(monkeypatch):
    pull_request = GithubEvent(
        id="pr-456",
        title="Surface authored pull requests",
        url="https://github.com/benmezger/daily-summary/pull/456",
        created_at=datetime(2026, 9, 10, 8, 0, 0),
        updated_at=datetime(2026, 9, 11, 12, 0, 0),
        repository=Repository(owner="benmezger", name="daily-summary"),
        event_type=EventType.PULL_REQUEST,
        state="MERGED",
    )

    class FakeGithub:
        def __init__(self, access_token: str, username: str) -> None:
            self.username = username

        def get_user(self) -> Account:
            return Account(login="benmezger", name="Ben Mezger")

        def issues_from(
            self,
            created_at: datetime,
            excluded_repositories: list[str],
            excluded_organizations: list[str],
        ) -> Iterator[GithubEvent]:
            return iter(())

        def pull_requests_from(
            self,
            updated_at: datetime,
            excluded_repositories: list[str],
            excluded_organizations: list[str],
        ) -> Iterator[GithubEvent]:
            return iter((pull_request,))

        async def commits_from(
            self,
            created_at: datetime,
            excluded_repositories: list[str],
            excluded_organizations: list[str],
        ) -> AsyncIterator[GithubEvent]:
            if False:
                yield pull_request

        def reviews_from(
            self,
            updated_at: datetime,
            excluded_repositories: list[str],
            excluded_organizations: list[str],
        ) -> Iterator[GithubEvent]:
            return iter(())

        def tags_from(
            self,
            created_at: datetime,
            excluded_repositories: list[str],
            excluded_organizations: list[str],
        ) -> Iterator[GithubEvent]:
            return iter(())

        def comments_from(
            self,
            created_at: datetime,
            excluded_repositories: list[str],
            excluded_organizations: list[str],
        ) -> Iterator[GithubEvent]:
            return iter(())
    monkeypatch.setattr("daily._cli.Github", FakeGithub)
    monkeypatch.setattr("daily._cli.Github", FakeGithub)
    runner = CliRunner()
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "--token",
            "token",
            "--username",
            "benmezger",
            "--file",
            "-",
            "daily-summary",
            "--date",
            "2026-09-11",
            "--no-ollama",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "_PR/Issue summary_" in result.output
    assert (
        "Surface authored pull requests "
        "[[PR](https://github.com/benmezger/daily-summary/pull/456)] "
        "/ [Merged]"
    ) in result.output
