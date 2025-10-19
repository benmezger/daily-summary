#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-02-28 Fri 23:18>

import re
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Self, Union

from pydantic import (
    AliasChoices,
    AliasPath,
    BaseModel,
    BeforeValidator,
    Field,
    model_validator,
)


class Account(BaseModel):
    username: str = Field(alias="login")
    name: str

    def __str__(self) -> str:
        return f"{self.name} - @{self.username}"


class EventType(StrEnum):
    PULL_REQUEST = "PR"
    ISSUE = "Issue"
    COMMIT = "Commit"
    REVIEW = "Review"
    TAG = "Tag"


class Repository(BaseModel):
    name: str
    owner: str

    @staticmethod
    def split_name_with_owner(
        value: Union[dict, "Repository"],
    ) -> Union[dict, "Repository"]:
        if isinstance(value, Repository):
            return value

        if not (name_with_owner := value.pop("nameWithOwner", None)):
            name_with_owner = value.pop("full_name")

        organization, repository_name = re.search(
            r"([^/]+)/([^/]+)", name_with_owner
        ).groups()

        return {"name": repository_name, "owner": organization}

    @property
    def repository_url(self) -> str:
        return f"https://github.com/{self}"

    def __str__(self) -> str:
        return f"{self.owner}/{self.name}"


class GithubReview(BaseModel):
    username: str = Field(
        validation_alias=AliasChoices("login", AliasPath("author", "login"))
    )
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    state: str


class GithubEvent(BaseModel):
    id: str = Field(validation_alias=AliasChoices("id", "node_id"))
    title: str = Field(
        validation_alias=AliasChoices("title", AliasPath("commit", "message"))
    )
    description: str | None = Field(
        default=None, validation_alias=AliasChoices("body", "description")
    )
    merged: Annotated[bool | None, BeforeValidator(lambda value: bool(value))] = Field(
        default=None, alias="mergedAt"
    )
    url: str = Field(validation_alias=AliasChoices("html_url", "url"))
    created_at: datetime = Field(
        validation_alias=AliasChoices(
            "created_at", "createdAt", AliasPath("commit", "committer", "date")
        )
    )
    updated_at: datetime | None = Field(default=None, alias="updatedAt")
    repository: Annotated[
        Repository, BeforeValidator(Repository.split_name_with_owner)
    ] = Field(validation_alias=AliasChoices("repository", "full_name"))
    sha: str | None = None
    event_type: EventType
    state: str | None = None
    reviews: list[GithubReview] = Field(
        default_factory=list[GithubReview],
        validation_alias=AliasChoices("nodes", AliasPath("reviews", "nodes")),
    )

    @model_validator(mode="before")
    @classmethod
    def set_event_type(cls: type["GithubEvent"], data: dict) -> dict:
        if data.get("event_type"):
            return data

        event_type = EventType.ISSUE

        if data.get("reviews"):
            event_type = EventType.REVIEW
        elif data.get("sha"):
            event_type = EventType.COMMIT
        elif "pr" in data.get("id", "").lower()[:2]:
            event_type = EventType.PULL_REQUEST

        data["event_type"] = event_type
        return data

    def __str__(self) -> str:
        return f"{self.title} @{self.repository} - {self.created_at}"


class Summary(BaseModel):
    title: str
    description: str | None
    repository_url: str
    event_url: str
    event_type: EventType
    organization: str
    state: str | None

    @classmethod
    def from_event(cls: type[Self], event: GithubEvent) -> Self:
        return cls(
            title=event.title.strip().splitlines()[0],
            repository_url=event.repository.repository_url,
            event_url=event.url.strip(),
            event_type=event.event_type,
            organization=str(event.repository),
            state=event.state.title() if event.state else None,
            description=event.description,
        )


class RepositoryEvents(BaseModel):
    repository: str
    organization: str
    events: list[GithubEvent] = Field(default_factory=list[GithubEvent])
