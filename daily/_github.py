#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-02-28 Fri 23:17>


import re
from collections.abc import Iterable
from datetime import date

import github
import pydash

from daily.models import EventType, GithubEvent, User


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
    ) -> Iterable[GithubEvent]:
        query = f"author:{self.username} created:{created_at:%Y-%m-%d}"

        for issue in self._github.search_issues(query):
            # we use the following regex to avoid using issue.pull_request
            # since it makes a request to it
            organization, repository_name = re.search(
                r"github\.com/([^/]+)/([^/]+)", issue.html_url
            ).groups()

            merged = bool(pydash.get(issue, "pull_request.merged_at", False))
            yield GithubEvent(
                title=issue.title,
                description=issue.body,
                organization=organization,
                merged=merged,
                url=issue.html_url,
                created_at=issue.created_at,
                updated_at=issue.updated_at,
                repository=repository_name,
                event_type=EventType.PULL_REQUEST
                if "pr_" in issue.node_id.lower()
                else EventType.ISSUE,
                state="merged" if merged else issue.state,
            )

    def commits_from(
        self,
        created_at: date,
    ) -> Iterable[GithubEvent]:
        query = f"author:{self.username} committer-date:{created_at:%Y-%m-%d}"

        for commit in self._github.search_commits(query, sort="committer-date"):
            title: str
            description: str | None = None

            if len(parts := commit.commit.message.splitlines()) > 1:
                title = parts[0]
                description = "".join(parts[1:])
            else:
                title = parts[0]

            yield GithubEvent(
                title=title,
                description=description,
                sha=commit.sha,
                url=commit.html_url,
                repository=commit.repository.name,
                organization=commit.repository.full_name.split("/")[0],
                created_at=commit.commit.author.date,
                event_type=EventType.COMMIT,
            )
