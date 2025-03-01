#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-02-28 Fri 23:18>

from datetime import datetime
from pydantic import BaseModel


class User(BaseModel):
    username: str
    name: str


class PR(BaseModel):
    title: str
    description: str
    organization: str | None = None
    merged: bool
    url: str
    created_at: datetime
    updated_at: datetime
    repository: str

    def __str__(self) -> str:
        return f"{self.title} @{self.repository} - {self.created_at}"
