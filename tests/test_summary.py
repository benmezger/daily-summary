#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-03-16 Sun 11:46>

import io
from datetime import date

import pytest
from snapshottest.pytest import SnapshotTest

from daily._summary import (
    maybe_write_github_summaries,
    maybe_write_header,
    maybe_write_misc,
)
from daily.models import RepositoryEvents, User


def test_maybe_write_header(account: User, repository_events: list[RepositoryEvents]):
    file = io.StringIO()

    maybe_write_header(account, repository_events, file, date(2025, 3, 16), False)
    file.seek(0)

    assert (
        file.read()
        == "Summary of *2025-03-16*\n"
        + "From [`benmezger`](https://github.com/benmezger)\n"
    )


def test_maybe_write_header_skips_on_empty_events(account: User):
    file = io.StringIO()
    maybe_write_header(account, [], file, date(2025, 3, 16))
    file.seek(0)

    assert file.read() == ""


@pytest.mark.parametrize(("escape",), ((False,), (True,)))
def test_maybe_write_github_summaries(
    escape: bool, repository_events: list[RepositoryEvents], snapshot: SnapshotTest
):
    file = io.StringIO()
    maybe_write_github_summaries(
        repository_events, file=file, ollama=None, escape=escape
    )
    file.seek(0)

    snapshot.assert_match(file.read())


def test_maybe_write_github_summaries_skips_on_empty_events():
    file = io.StringIO()
    maybe_write_github_summaries([], file=file, ollama=None)
    file.seek(0)

    assert file.read() == ""


def test_maybe_write_misc(
    repository_events: list[RepositoryEvents], snapshot: SnapshotTest
):
    file = io.StringIO()
    maybe_write_misc(repository_events, file=file)
    file.seek(0)

    snapshot.assert_match(file.read())


def test_maybe_write_misc_skips_on_empty_events():
    file = io.StringIO()
    maybe_write_misc([], file=file)
    file.seek(0)

    assert file.read() == ""
