#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-02-28 Fri 23:17>


from datetime import date
from typing import Iterable
import github
import pydash

from daily.models import Issue, User


class Github:
    def __init__(self, access_token: str) -> None:
        auth = github.Auth.Token(access_token)

        self._github = github.Github(auth=auth)
        self._user = self._github.get_user()

    def get_user(self) -> User:
        assert self._user.name
        return User(username=self._user.login, name=self._user.name)

    def issues_from(
        self,
        created_at: date,
        organization: str | None = None,
    ) -> Iterable[Issue]:
        query = f"author:{self._user.login} created:{created_at:%Y-%m-%d}"
        if organization:
            query = f"{query} org:{organization}"

        for issue in self._github.search_issues(query):
            yield Issue(
                title=issue.title,
                description=issue.body,
                organization=organization,
                merged=bool(pydash.get(issue, "pull_request.merged_at", False)),
                url=issue.url,
                created_at=issue.created_at,
                updated_at=issue.updated_at,
                repository=issue.repository.name,
            )
