#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-03-01 Sat 17:44>

import datetime
import re
from collections import defaultdict
from functools import partial
from typing import TextIO

from .models import Account, EventType, GithubEvent, RepositoryEvents, Summary
from .ollama import Ollama


def maybe_write_header(
    account: Account,
    events: list[RepositoryEvents],
    file: TextIO,
    date: datetime.date,
    escape: bool = False,
) -> None:
    if not events:
        return

    file.write(f"Summary of *{date:%Y-%m-%d}*\n")
    file.write(
        "From "
        + _maybe_escape_str(
            f"[`{account.username}`](https://github.com/{account.username})\n", escape
        )
    )


def maybe_write_github_summaries(
    repository_events: list[RepositoryEvents],
    ollama: Ollama | None,
    file: TextIO,
    escape: bool = False,
) -> None:
    summary = partial(_maybe_write_summary, file=file, escape=escape, ollama=ollama)

    sections = [
        ("\n_PR/Issue summary_\n", (EventType.ISSUE, EventType.PULL_REQUEST)),
        ("\n_PR/Issue review_\n", (EventType.REVIEW,)),
        ("\n_Tags summary_\n", (EventType.TAG,)),
        ("\n_Comments summary_\n", (EventType.COMMENT,)),
    ]

    for title, event_types in sections:
        summary(
            title=title,
            repository_events=_order_by_org_event_type(repository_events, event_types),
        )

    for title, committed_by_others in (
        ("\n_Commit summary_\n", False),
        ("\n_Committed by others (unverified)_\n", True),
    ):
        summary(
            title=title,
            repository_events=_order_by_org_event_type(
                repository_events,
                (EventType.COMMIT,),
                committed_by_others=committed_by_others,
            ),
        )


def maybe_write_misc(events: list[RepositoryEvents], file: TextIO) -> None:
    if not events:
        return

    file.write("\n_Misc_\n")
    file.write("\n- PR reviews and discussions\n")
    file.write("\n")
    file.write("Created by https://github.com/benmezger/daily-summary\n")


def _maybe_summarize(content: str, ollama: Ollama | None) -> str:
    if ollama:
        return ollama.chat(
            f"Summarize this message using imperative mood in a single sentence: "
            f"{content}"
        )

    return content


def _write_repository_section(
    repository: str,
    events: list[GithubEvent],
    ollama: Ollama | None,
    file: TextIO,
    escape: bool = False,
) -> None:
    repository_url = events[0].repository.repository_url
    file.write(_maybe_escape_str(f"- [`{repository}`]({repository_url})\n", escape))
    _write_events(events, ollama, file, escape)


def _write_events(
    events: list[GithubEvent],
    ollama: Ollama | None,
    file: TextIO,
    escape: bool = False,
) -> None:
    for evt in events:
        summary = Summary.from_event(evt)
        summarized_title = _maybe_summarize(summary.title, ollama)
        state_suffix = f"/ [{summary.state}]\n" if summary.state else "\n"

        file.write(
            _maybe_escape_str(f"  - {summarized_title} ", escape)
            + f"[[{summary.event_type.value}]({summary.event_url})] "
            f"{state_suffix}"
        )


def _maybe_write_summary(
    title: str,
    repository_events: defaultdict[str, defaultdict[str, list[GithubEvent]]],
    ollama: Ollama | None,
    file: TextIO,
    escape: bool = False,
) -> None:
    if not repository_events:
        return

    file.write(title)

    for organization, repo_events in repository_events.items():
        file.write(
            _maybe_escape_str(
                f"\n[`{organization}`](https://github.com/{organization})\n", escape
            )
        )

        for repository, events in repo_events.items():
            _write_repository_section(repository, events, ollama, file, escape)


def _order_by_org_event_type(
    repository_events: list[RepositoryEvents],
    event_types: tuple[EventType, ...],
    committed_by_others: bool | None = None,
) -> defaultdict[str, defaultdict[str, list[GithubEvent]]]:
    """
    Order and filter repository events by organization and repository.

    Args:
        committed_by_others: If None, no filtering on this field.
            If True/False, only include events matching that value.

    Returns a nested defaultdict structure:
        {"organization": {"repository": [filtered_events]}}
    """

    events = defaultdict(lambda: defaultdict(list))
    for evt in repository_events:
        filtered_events = [
            e
            for e in evt.events
            if e.event_type in event_types
            and (
                committed_by_others is None
                or e.committed_by_others == committed_by_others
            )
        ]
        if filtered_events:
            events[evt.organization][evt.repository].extend(filtered_events)

    return events


def _maybe_escape_str(s: str, escape: bool) -> str:
    if not escape:
        return s

    s = s.replace('"', '\\"').replace("`", "\\`")
    # make sure we skip any #1, #23, etc. to avoid linking with issue.
    return re.sub(r"#\d+", _re_maybe_escape_hash, s)


def _re_maybe_escape_hash(match_: re.Match[str]) -> str:
    if matched := match_.group(0):
        return matched.replace("#", "#&NoBreak;")
    return matched
