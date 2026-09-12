#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>

from collections.abc import AsyncIterator, Iterator
from datetime import datetime

from click.testing import CliRunner

from daily._cli import cli
from daily.github import Github
from daily.models import Account, EventType, GithubEvent, Repository


def test_make_paginated_graphql_request_fetches_all_pages(monkeypatch):
    github = Github("token", username="benmezger")
    queries: list[str] = []
    responses = iter(
        (
            {
                "data": {
                    "search": {
                        "edges": [
                            {
                                "node": {
                                    "id": "issue-1",
                                    "title": "First page issue",
                                    "url": "https://github.com/benmezger/daily-summary/issues/1",
                                    "createdAt": "2026-09-11T07:00:00",
                                    "repository": {
                                        "nameWithOwner": "benmezger/daily-summary"
                                    },
                                    "state": "OPEN",
                                }
                            }
                        ],
                        "pageInfo": {"hasNextPage": True, "endCursor": "cursor-1"},
                    }
                }
            },
            {
                "data": {
                    "search": {
                        "edges": [
                            {
                                "node": {
                                    "id": "issue-2",
                                    "title": "Second page issue",
                                    "url": "https://github.com/benmezger/daily-summary/issues/2",
                                    "createdAt": "2026-09-11T08:00:00",
                                    "repository": {
                                        "nameWithOwner": "benmezger/daily-summary"
                                    },
                                    "state": "OPEN",
                                }
                            }
                        ],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    }
                }
            },
        )
    )

    class FakeResponse:
        def __init__(self, payload: dict) -> None:
            self._payload = payload

        def json(self) -> dict:
            return self._payload

    def fake_make_request(self, method: str, url: str, json: dict | None = None):
        queries.append(json["query"])
        return FakeResponse(next(responses))

    monkeypatch.setattr(Github, "_make_request", fake_make_request)

    result = github._make_paginated_graphql_request(
        lambda after: (
            "{ search(query: \"author:benmezger is:issue\", type: ISSUE, "
            f"first: 100, after: {after}) "
            "{ edges { node { id title url createdAt repository { nameWithOwner } "
            "} } pageInfo { hasNextPage endCursor } } }"
        ),
        path="data.search",
    )

    assert [event.id for event in result] == ["issue-1", "issue-2"]
    assert queries == [
        '{ search(query: "author:benmezger is:issue", type: ISSUE, first: 100, '
        "after: null) { edges { node { id title url createdAt repository { "
        'nameWithOwner } } } pageInfo { hasNextPage endCursor } } }',
        '{ search(query: "author:benmezger is:issue", type: ISSUE, first: 100, '
        'after: "cursor-1") { edges { node { id title url createdAt repository '
        '{ nameWithOwner } } } pageInfo { hasNextPage endCursor } } }',
    ]


def test_issues_from_includes_updated_pull_requests(monkeypatch):
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
    issue = GithubEvent(
        id="issue-123",
        title="Track daily summary regression",
        url="https://github.com/benmezger/daily-summary/issues/123",
        created_at=datetime(2026, 9, 11, 7, 0, 0),
        repository=Repository(owner="benmezger", name="daily-summary"),
        event_type=EventType.ISSUE,
        state="OPEN",
    )
    queries: list[tuple[str, str]] = []

    def fake_make_paginated_graphql_request(self, query_factory, path: str):
        graphql_query = query_factory("null")
        queries.append((graphql_query, path))
        if "is:issue" in graphql_query:
            return [issue, pull_request]
        if (
            "updated:2026-09-11T00:00:00..2026-09-11T23:59:59 is:pr"
            in graphql_query
        ):
            return [pull_request]
        return []

    monkeypatch.setattr(
        Github,
        "_make_paginated_graphql_request",
        fake_make_paginated_graphql_request,
    )

    result = list(github.issues_from(datetime(2026, 9, 11), [], []))

    assert result == [issue, pull_request]
    assert queries == [
        (
            """
{
  search(
    query: "author:benmezger created:2026-09-11 is:issue"
    type: ISSUE
    first: 100
    after: null
  ) {
    edges {
      node {
        ... on Issue {
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
        }
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
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
""",
            "data.search",
        ),
        (
            """
{
  search(
    query: "author:benmezger updated:2026-09-11T00:00:00..2026-09-11T23:59:59 is:pr"
    type: ISSUE
    first: 100
    after: null
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
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
""",
            "data.search",
        ),
    ]


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
