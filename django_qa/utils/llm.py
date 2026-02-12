from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.conf import settings
import httpx
from openai import OpenAI

_HTTP_CLIENT = httpx.Client(timeout=httpx.Timeout(60.0), trust_env=True)


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


def _qwen_client() -> tuple[OpenAI, str]:
    api_key = getattr(settings, "QWEN_API_KEY", "") or ""
    base_url = getattr(settings, "QWEN_API_BASE", "") or ""
    model = getattr(settings, "QWEN_MODEL_NAME", "") or ""
    client = OpenAI(api_key=api_key, base_url=base_url, http_client=_HTTP_CLIENT)
    return client, model


def chat(messages: list[LLMMessage], temperature: float = 0.2) -> str:
    model_name = getattr(settings, "CURRENT_LLM_MODEL", "qwen") or "qwen"
    if model_name == "qwen":
        client, model = _qwen_client()
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
        )
        return (resp.choices[0].message.content or "").strip()

    raise ValueError(f"不支持的模型配置: CURRENT_LLM_MODEL={model_name!r}")
