#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-02-28 Fri 23:18>

from datetime import datetime
from pydantic import BaseModel
from ._ollama import Ollama


class User(BaseModel):
    username: str
    name: str

    def __str__(self) -> str:
        return f"{self.name} - @{self.username}"


class Issue(BaseModel):
    title: str
    description: str | None
    organization: str | None = None
    merged: bool
    url: str
    created_at: datetime
    updated_at: datetime
    repository: str
    is_pr: bool

    def __str__(self) -> str:
        return f"{self.title} @{self.repository} - {self.created_at}"

    def summarize(self, ollama: Ollama) -> str:
        return ollama.chat(
            f"Summarize this message using imperative mood in a single sentence: "
            f"{self.title}"
        )
