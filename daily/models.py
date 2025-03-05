#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-02-28 Fri 23:18>

from datetime import datetime
from enum import Enum
from typing import Annotated, Self

from pydantic import BaseModel, BeforeValidator, Field

from ._ollama import Ollama


class User(BaseModel):
    username: str
    name: str

    def __str__(self) -> str:
        return f"{self.name} - @{self.username}"


class EventType(str, Enum):
    PULL_REQUEST = "PR"
    ISSUE = "Issue"
    COMMIT = "Commit"


class GithubEvent(BaseModel):
    title: str
    description: str | None
    organization: str
    merged: bool | None = None
    url: str
    created_at: datetime
    updated_at: datetime | None = None
    repository: str
    sha: str | None = None
    event_type: EventType
    state: str | None = None

    def __str__(self) -> str:
        return f"{self.title} @{self.repository} - {self.created_at}"

    def summarize(self, ollama: Ollama) -> str:
        return ollama.chat(
            f"Summarize this message using imperative mood in a single sentence: "
            f"{self.title}"
        )


class Summary(BaseModel):
    title: Annotated[
        str,
        BeforeValidator(lambda value: value.replace('"', '\\"').replace("`", "\\`")),
    ]
    url: str
    event_type: EventType
    organization: str
    state: str | None

    @classmethod
    def from_event(cls: type[Self], event: GithubEvent, ollama: Ollama | None) -> Self:
        title = event.title
        if event.event_type in (EventType.ISSUE, EventType.PULL_REQUEST) and ollama:
            title = event.summarize(ollama)

        return cls(
            title=title.strip(),
            url=event.url.strip(),
            event_type=event.event_type,
            organization=event.organization,
            state=event.state,
        )


class RepositoryEvents(BaseModel):
    repository: str
    organization: str
    events: list[GithubEvent] = Field(default_factory=list[GithubEvent])
