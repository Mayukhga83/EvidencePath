from __future__ import annotations

import json
import re
from typing import Type, TypeVar

from pydantic import BaseModel

from graphmind.config import settings

T = TypeVar("T", bound=BaseModel)


def _client():
    if not settings.has_openai:
        return None
    try:
        from openai import OpenAI

        return OpenAI(api_key=settings.openai_api_key)
    except Exception:
        return None


def structured_call(schema: Type[T], system_prompt: str, user_prompt: str) -> T | None:
    client = _client()
    if client is None:
        return None
    try:
        response = client.responses.parse(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=schema,
        )
        return response.output_parsed
    except Exception:
        try:
            response = client.responses.create(
                model=settings.openai_model,
                input=[
                    {"role": "system", "content": system_prompt + " Return valid JSON only."},
                    {"role": "user", "content": user_prompt},
                ],
            )
            match = re.search(r"\{.*\}", response.output_text, re.DOTALL)
            payload = match.group(0) if match else response.output_text
            return schema.model_validate(json.loads(payload))
        except Exception:
            return None


def text_call(system_prompt: str, user_prompt: str) -> str | None:
    client = _client()
    if client is None:
        return None
    try:
        response = client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.output_text.strip()
    except Exception:
        return None
