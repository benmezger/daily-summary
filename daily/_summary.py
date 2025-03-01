#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-03-01 Sat 17:44>

from typing import TextIO

from pydantic.main import BaseModel


class Summary(BaseModel):
    summary: str
    pr_url: str


def write_summary(repository_summaries: dict[str, list[Summary]], file: TextIO) -> None:
    file.write("_Engineering_\n")

    for repository, summaries in repository_summaries.items():
        file.write(f"* `{repository}`\n")
        for summary in summaries:
            file.write(f"    ** {summary.summary} [PR]({summary.pr_url})\n")

    file.write("_Meetings_\n")
    file.write("    * \n")

    file.write("_Misc_\n")
    file.write("    * PR reviews and discussions\n")
