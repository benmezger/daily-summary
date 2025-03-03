#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-02-28 Fri 23:18>

from datetime import datetime
from enum import Enum
from typing import Self

from pydantic import BaseModel
from pydantic.fields import Field

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

    def __str__(self) -> str:
        return f"{self.title} @{self.repository} - {self.created_at}"

    def summarize(self, ollama: Ollama) -> str:
        return ollama.chat(
            f"Summarize this message using imperative mood in a single sentence: "
            f"{self.title}"
        )


class Summary(BaseModel):
    summary: str
    url: str
    event_type: EventType
    organization: str

    @classmethod
    def from_event(cls: type[Self], event: GithubEvent, ollama: Ollama | None) -> Self:
        if event.event_type in (EventType.ISSUE, EventType.PULL_REQUEST):
            return cls(
                summary=(event.summarize(ollama) if ollama else event.title).strip(),
                url=event.url.strip(),
                event_type=event.event_type,
                organization=event.organization,
            )

        return cls(
            summary=event.title,
            url=event.url,
            event_type=event.event_type,
            organization=event.organization,
        )


class RepositoryEvents(BaseModel):
    repository: str
    organization: str
    events: list[GithubEvent] = Field(default_factory=list[GithubEvent])
