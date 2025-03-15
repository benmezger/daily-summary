#!/usr/bin/env python3

# Author: Ben Mezger <me@benmezger.nl>
# Created at <2025-03-01 Sat 12:56>

from ollama import Client


class Ollama:
    def __init__(self, host: str, model: str = "mistral") -> None:
        self._model = model
        self.client = Client(host=host)

    def chat(self, message: str) -> str:
        response = self.client.chat(
            model=self._model, messages=[{"role": "user", "content": message}]
        )
        return response.message.content or ""
