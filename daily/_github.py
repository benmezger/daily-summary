#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-02-28 Fri 23:17>


import re
from collections.abc import Iterable
from datetime import date

import github
import pydash

from daily.models import Issue, User


class Github:
    def __init__(self, access_token: str, username: str) -> None:
        auth = github.Auth.Token(access_token)

        self.username = username
        self._github = github.Github(auth=auth)
        self._user = self._github.get_user()

    def get_user(self) -> User:
        assert self._user.name
        return User(username=self._user.login, name=self._user.name)

    def issues_from(
        self,
        created_at: date,
    ) -> Iterable[Issue]:
        query = f"author:{self.username} created:{created_at:%Y-%m-%d}"

        for issue in self._github.search_issues(query):
            # we use the following regex to avoid using issue.pull_request
            # since it makes a request to it
            organization, repository_name = re.search(
                r"github\.com/([^/]+)/([^/]+)", issue.html_url
            ).groups()

            yield Issue(
                title=issue.title,
                description=issue.body,
                organization=organization,
                merged=bool(pydash.get(issue, "pull_request.merged_at", False)),
                url=issue.html_url,
                created_at=issue.created_at,
                updated_at=issue.updated_at,
                repository=repository_name,
                is_pr="pr_" in issue.node_id.lower(),
            )
