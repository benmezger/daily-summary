#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-02-28 Fri 23:17>


from collections.abc import Iterable
from datetime import date

import pydash
from httpx import Client

from . import _graphql_queries as queries
from ._models import GithubEvent, User


class Github:
    def __init__(self, access_token: str, username: str) -> None:
        self._client = Client(
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
        )

        self.username = username
        self._user: User | None = None

    def get_user(self) -> User:
        if self._user:
            return self._user

        response = self._client.get("https://api.github.com/user")
        response.raise_for_status()
        return User.model_validate(response.json())

    def issues_from(
        self,
        created_at: date,
    ) -> Iterable[GithubEvent]:
        yield from self._make_graphql_request(
            "https://api.github.com/graphql",
            queries.issues.format(
                username=self.username,
                created_at=f"{created_at:%Y-%m-%d}",
            ),
            path="data.search.edges",
        )

    def commits_from(
        self,
        created_at: date,
    ) -> Iterable[GithubEvent]:
        query = (
            f"author:{self.username}+committer-date:{created_at:%Y-%m-%d}"
            "+sort:committer-date"
        )
        response = self._client.get(f"https://api.github.com/search/commits?q={query}")
        response.raise_for_status()

        for item in pydash.get(response.json(), "items", []):
            yield GithubEvent.model_validate(item)

    def _make_graphql_request(
        self, url: str, query: str, path: str
    ) -> list[GithubEvent]:
        response = self._client.post(url, json={"query": query})
        response.raise_for_status()

        results = list[GithubEvent]()
        for edge in pydash.get(response.json(), path, []):
            if node := pydash.get(edge, "node", None):
                results.append(GithubEvent.model_validate(node))

        return results
