#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-03-01 Sat 17:44>

from collections import defaultdict
from datetime import datetime
from typing import TextIO

from daily.models import EventType, GithubEvent, RepositoryEvents, Summary

from ._ollama import Ollama


def maybe_write_header(events: list[RepositoryEvents], file: TextIO) -> None:
    if not events:
        return

    file.write(f"Summary of *{datetime.now():%Y-%m-%d}*\n")


def maybe_write_issue_summary(
    repository_events: list[RepositoryEvents], ollama: Ollama | None, file: TextIO
) -> None:
    issue_events = _order_by_org_event_type(
        repository_events, (EventType.ISSUE, EventType.PULL_REQUEST)
    )
    if not issue_events:
        return

    file.write("\n_PR/Issues summary_\n")

    for organization, repo_events in issue_events.items():
        file.write(f"\n\\`{organization}\\`\n")

        for repository, events in repo_events.items():
            file.write(f"\n- \\`{repository}\\`\n")

            for evt in events:
                summary = Summary.from_event(evt, ollama)
                title = summary.summary.replace('"', '\\"').replace("`", "\\`")
                file.write(
                    f"  - {title} [[{summary.event_type.value}]({summary.url})]\n"
                )


def maybe_write_misc(events: list[RepositoryEvents], file: TextIO) -> None:
    if not events:
        return

    file.write("\n_Misc_\n")
    file.write("\n- PR reviews and discussions\n")


def maybe_write_commit_summary(
    repository_events: list[RepositoryEvents], file: TextIO
) -> None:
    commit_events = _order_by_org_event_type(repository_events, (EventType.COMMIT,))
    if not commit_events:
        return

    file.write("\n_Commit summary_\n")

    for organization, repo_events in commit_events.items():
        file.write(f"\n\\`{organization}\\`\n")

        for repository, events in repo_events.items():
            file.write(f"\n- \\`{repository}\\`\n")

            for evt in events:
                summary = Summary.from_event(evt, None)
                title = summary.summary.replace('"', '\\"').replace("`", "\\`")
                file.write(
                    f"  - {title} [[{summary.event_type.value}]({summary.url})]\n"
                )


def _order_by_org_event_type(
    repository_events: list[RepositoryEvents], event_types: tuple[EventType, ...]
) -> defaultdict[str, defaultdict[str, list[GithubEvent]]]:
    """
    Order and filter repository events by organization and repository.

    Returns a nested defaultdict structure:
        {"organization": {"repository": [filtered_events]}}
    """

    events = defaultdict(lambda: defaultdict(list))
    for evt in repository_events:
        filtered_events = [e for e in evt.events if e.event_type in event_types]
        if filtered_events:
            events[evt.organization][evt.repository].extend(filtered_events)

    return events
