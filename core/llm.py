"""One place to call NVIDIA Nemotron models on Nebius Token Factory.

Token Factory speaks the OpenAI API format, so we use the official `openai`
library and just point it at Nebius.

Usage:
    from core.llm import chat, chat_json
    text = chat("nano", [{"role": "user", "content": "Hello"}])
"""
import json
import re
from functools import lru_cache

from openai import OpenAI
from pydantic import BaseModel

from core import config

# Short names we use in code -> exact model IDs on Token Factory.
MODELS = {
    "nano": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",       # fast, cheap: profile extraction, follow-ups
    "super": "nvidia/nemotron-3-super-120b-a12b",           # balanced: rules extraction
    "ultra": "nvidia/Nemotron-3-Ultra-550b-a55b",           # strongest reasoning: eligibility, appeals
    "lightning": "nvidia/Nemotron-3_5-Lightning",           # newest, low latency (evaluating)
    # Helper, not a Nemotron: no NVIDIA vision model is on Token Factory yet. Only used to read
    # text off a photo of a letter; all understanding and decisions stay with Nemotron.
    "vision": "google/gemma-3-27b-it",
}

# Some reasoning models put their "thinking" inside <think>...</think> in the reply.
THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)
# Pull JSON out of ```json ... ``` fences if the model adds them.
JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


@lru_cache  # create the client once and reuse it
def client() -> OpenAI:
    # The SDK's default timeout is 10 minutes (plus retries) — far too long for a web app.
    # 2 minutes covers Ultra's longest answers; a stuck request then fails and is retried.
    return OpenAI(api_key=config.NEBIUS_API_KEY, base_url=config.NEBIUS_BASE_URL, timeout=120, max_retries=2)


def model_id(name: str) -> str:
    return MODELS.get(name, name)  # accept short names or full IDs


def complete(model: str, messages: list[dict], thinking: bool = True, **kwargs):
    """Raw API call. Returns the full response object (useful for tool calls and token usage).

    Nemotron 3 models "think" (reason step by step) before answering. That helps hard tasks,
    but simple ones (short questions, extracting a few facts) are faster and cheaper without it.
    `thinking=False` turns it off. Thinking tokens also count towards max_tokens, so a long
    think can use them all and leave an empty answer.
    """
    if not thinking:
        kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
    return client().chat.completions.create(model=model_id(model), messages=messages, **kwargs)


def chat(model: str, messages: list[dict], **kwargs) -> str:
    """Send messages, return only the final answer text (thinking removed)."""
    response = complete(model, messages, **kwargs)
    text = response.choices[0].message.content or ""
    return THINK_BLOCK.sub("", text).strip()


def chat_json(model: str, messages: list[dict], schema: type[BaseModel] | None = None, **kwargs) -> dict:
    """Like chat(), but parses the answer as JSON. Raises ValueError if it isn't valid JSON.

    Pass a Pydantic `schema` to use structured output: the API then forces the answer
    to match that exact JSON shape (recommended whenever thinking=False).
    """
    if schema is not None:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": schema.__name__, "schema": schema.model_json_schema(), "strict": True},
        }
    kwargs.setdefault("temperature", 0)
    text = chat(model, messages, **kwargs)
    fenced = JSON_FENCE.search(text)
    if fenced:
        text = fenced.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Model did not return JSON: {text[:200]}")
    return json.loads(text[start : end + 1])
