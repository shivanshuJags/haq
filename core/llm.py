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

from core import config

# Short names we use in code -> exact model IDs on Token Factory.
MODELS = {
    "nano": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",       # fast, cheap: profile extraction, follow-ups
    "super": "nvidia/nemotron-3-super-120b-a12b",           # balanced: rules extraction
    "ultra": "nvidia/Nemotron-3-Ultra-550b-a55b",           # strongest reasoning: eligibility, appeals
    "lightning": "nvidia/Nemotron-3_5-Lightning",           # newest, low latency (evaluating)
}

# Some reasoning models put their "thinking" inside <think>...</think> in the reply.
THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)
# Pull JSON out of ```json ... ``` fences if the model adds them.
JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


@lru_cache  # create the client once and reuse it
def client() -> OpenAI:
    return OpenAI(api_key=config.NEBIUS_API_KEY, base_url=config.NEBIUS_BASE_URL)


def model_id(name: str) -> str:
    return MODELS.get(name, name)  # accept short names or full IDs


def complete(model: str, messages: list[dict], **kwargs):
    """Raw API call. Returns the full response object (useful for tool calls and token usage)."""
    return client().chat.completions.create(model=model_id(model), messages=messages, **kwargs)


def chat(model: str, messages: list[dict], **kwargs) -> str:
    """Send messages, return only the final answer text (thinking removed)."""
    response = complete(model, messages, **kwargs)
    text = response.choices[0].message.content or ""
    return THINK_BLOCK.sub("", text).strip()


def chat_json(model: str, messages: list[dict], **kwargs) -> dict:
    """Like chat(), but parses the answer as JSON. Raises ValueError if it isn't valid JSON."""
    text = chat(model, messages, temperature=0, **kwargs)
    fenced = JSON_FENCE.search(text)
    if fenced:
        text = fenced.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Model did not return JSON: {text[:200]}")
    return json.loads(text[start : end + 1])
