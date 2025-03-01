#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-03-01 Sat 17:44>

from datetime import datetime
from typing import TextIO

from pydantic.main import BaseModel


class Summary(BaseModel):
    summary: str
    url: str
    is_pr: bool


def write_summary(repository_summaries: dict[str, list[Summary]], file: TextIO) -> None:
    file.write(f"Summary of *{datetime.now():%Y-%m-%d}*\n")
    file.write("\n_Engineering_\n")

    for repository, summaries in repository_summaries.items():
        file.write(f"\n`{repository}`\n")
        for summary in summaries:
            url_tag = "PR" if summary.is_pr else "Issue"
            file.write(f"- {summary.summary} [{url_tag}]({summary.url})\n")

    file.write("\n_Meetings_\n\n")
    file.write("- \n")

    file.write("\n_Misc_\n\n")
    file.write("- PR reviews and discussions\n")
