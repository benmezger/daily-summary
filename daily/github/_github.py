#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-02-28 Fri 23:17>


from collections.abc import Iterable
from datetime import datetime
from typing import Any, Literal, overload

import httpx
import pydash
import tenacity
from httpx import Client

from daily.models import Account, GithubEvent

from . import _graphql_queries as queries


class Github:
    def __init__(self, access_token: str, username: str) -> None:
        self._client = Client(
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
        )

        self.username = username
        self._account: Account | None = None

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(httpx.ReadTimeout),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    )
    def get_user(self) -> Account:
        if self._account:
            return self._account

        response = self._make_request("get", "https://api.github.com/user")
        return Account.model_validate(response.json())

    def issues_from(
        self,
        created_at: datetime,
    ) -> Iterable[GithubEvent]:
        yield from self._make_graphql_request(
            queries.issues.format(
                username=self.username,
                created_at=f"{created_at:%Y-%m-%d}",
            ),
            path="data.search.edges",
        )

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(httpx.ReadTimeout),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
    )
    def commits_from(
        self,
        created_at: datetime,
    ) -> Iterable[GithubEvent]:
        query = (
            f"author:{self.username}+committer-date:{created_at:%Y-%m-%d}"
            "+sort:committer-date"
        )

        response = self._make_request(
            "get", f"https://api.github.com/search/commits?q={query}"
        )

        for item in pydash.get(response.json(), "items", []):
            yield GithubEvent.model_validate(item)

    def reviews_from(self, updated_at: datetime) -> Iterable[GithubEvent]:
        for event in self._make_graphql_request(
            queries.reviews.format(
                username=self.username,
                updated_at=f"{updated_at:%Y-%m-%d}",
            ),
            path="data.search.edges",
        ):
            for review in event.reviews:
                if review.username != self.username:
                    continue
                if review.updated_at.date() != updated_at.date():
                    continue

                yield event
                break

    def tags_from(self, created_at: datetime) -> Iterable[GithubEvent]:
        response = self._make_request(
            "post",
            "https://api.github.com/graphql",
            json={"query": queries.tags.format()},
        )
        repositories: list = pydash.get(response, "data.viewer.repositories.nodes", [])

        for repo in repositories:
            repo_name = repo.get("nameWithOwner")

            for ref in pydash.get(repo, "refs.nodes", []):
                tag_name = ref.get("name")
                target = ref.get("target", {})

                # Get date from annotated tag or commit
                if tagger := target.get("tagger"):
                    tag_date = tagger.get("date")
                elif author := target.get("author"):
                    tag_date = author.get("date") or target.get("committedDate")
                else:
                    continue

                # Filter by created_at date
                tag_datetime = datetime.fromisoformat(tag_date)
                if tag_datetime.date() != created_at.date():
                    continue

                yield GithubEvent.model_validate(
                    {
                        "id": f"tag-{repo_name}-{tag_name}",
                        "title": f"Tagged {tag_name}",
                        "url": f"https://github.com/{repo_name}/releases/tag/{tag_name}",
                        "created_at": tag_date,
                        "repository": {"nameWithOwner": repo_name},
                        "event_type": "Tag",
                    }
                )

    def comments_from(self, created_at: datetime) -> Iterable[GithubEvent]:
        response = self._make_request(
            "post",
            "https://api.github.com/graphql",
            json={
                "query": queries.comments.format(
                    username=self.username,
                    updated_at=f"{created_at:%Y-%m-%d}",
                )
            },
        )

        for edge in pydash.get(response, "data.search.edges", []):
            node = edge.get("node", {})

            for comment in pydash.get(node, "comments.nodes", []):
                if pydash.get(comment, "author.login") != self.username:
                    continue

                comment_created_at = comment.get("createdAt")
                comment_datetime = datetime.fromisoformat(comment_created_at)

                if comment_datetime.date() != created_at.date():
                    continue

                yield GithubEvent.model_validate(
                    {
                        "id": f"comment-{node.get('id')}-"
                        f"{comment.get('url').split('#')[-1]}",
                        "title": f"Commented on: {node.get('title')}",
                        "body": comment.get("body"),
                        "url": comment.get("url"),
                        "created_at": comment_created_at,
                        "repository": {
                            "nameWithOwner": pydash.get(
                                node, "repository.nameWithOwner"
                            )
                        },
                        "state": node.get("state"),
                        "event_type": "Comment",
                    }
                )

    def _make_graphql_request(self, query: str, path: str) -> list[GithubEvent]:
        response = self._make_request(
            "post", "https://api.github.com/graphql", json={"query": query}
        )

        results = list[GithubEvent]()
        for edge in pydash.get(response, path, []):
            if node := pydash.get(edge, "node", None):
                results.append(GithubEvent.model_validate(node))

        return results

    @overload
    def _make_request(
        self, method: Literal["get"], url: str, json: Literal[None] = None
    ) -> httpx.Response: ...

    @overload
    def _make_request(
        self, method: Literal["post"], url: str, json: dict[str, Any]
    ) -> httpx.Response: ...

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(
            (httpx.ReadTimeout, httpx.HTTPStatusError)
        ),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=5),
    )
    def _make_request(
        self,
        method: Literal["post", "get"],
        url: str,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        kwargs = {}
        if method == "post":
            kwargs["json"] = json

        response: httpx.Response = getattr(self._client, method)(url=url, **kwargs)
        response.raise_for_status()

        return response
