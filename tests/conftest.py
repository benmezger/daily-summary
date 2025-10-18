#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-03-16 Sun 11:43>

from collections import defaultdict
from datetime import datetime

import pytest

from daily.models import EventType, GithubEvent, Repository, RepositoryEvents, User


@pytest.fixture
def account() -> User:
    return User(login="benmezger", name="Ben Mezger")


@pytest.fixture
def github_events() -> list[GithubEvent]:
    events = []
    for event_type in list(EventType):
        for i in range(2):
            events.append(
                GithubEvent(
                    id=f"id-{i}",
                    title=f"Title {event_type} {i}\nTitle body",
                    description="Event description",
                    url=f"http://github.com/repo/{event_type}",
                    event_type=event_type,
                    sha="sha-123" if event_type == EventType.COMMIT else None,
                    created_at=datetime(2025, 3, 16),
                    repository=Repository(
                        owner=f"repository-owner-{i}",
                        name=f"repository-name-{i}",
                    ),
                ),
            )
    return events


@pytest.fixture
def repository_events(
    github_events: list[GithubEvent],
) -> list[RepositoryEvents]:
    repository_events: dict[str, list[GithubEvent]] = defaultdict(list[GithubEvent])

    for event in github_events:
        repository_events[str(event.repository)].append(event)

    return [
        RepositoryEvents(
            repository=evts[0].repository.name,
            organization=evts[0].repository.owner,
            events=evts,
        )
        for evts in repository_events.values()
    ]
