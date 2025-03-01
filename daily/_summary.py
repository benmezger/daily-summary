#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-03-01 Sat 12:59>

from daily.models import PR
from ._ollama import Ollama


def summarize(prs: list[PR]) -> list[str]:
    ollama = Ollama()

    summaries = []
    for pr in prs:
        content = pr.title
        summaries.append(
            ollama.chat(
                f"Summarize this message in imperative mood in a "
                f"single sentence: {content}"
            )
        )

    return list(filter(None, summaries))
