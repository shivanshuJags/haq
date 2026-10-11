"""US-002 smoke test: can we talk to every Nemotron model, and can they do what Haq needs?

Run from the project root:
    python -m scripts.check_llm

Tests:
  1. Each model replies (and how fast)
  2. Nano turns a Hinglish sentence into a structured profile (JSON)
  3. Super can call a tool (needed for the agent)
"""
import json
import time

from core.llm import MODELS, chat, chat_json, complete

HINGLISH_INPUT = (
    "Main Bihar se hoon, 20 saal ki hoon, BA second year mein padh rahi hoon. "
    "Papa kisan hain, ghar ki saal ki income lagbhag 1.5 lakh hai. Hum OBC hain."
)

PROFILE_PROMPT = """Extract the person's profile from their message.
Return ONLY a JSON object with these keys (use null if not mentioned):
{"age": int, "gender": "male"|"female"|"other", "state": str, "is_student": bool,
 "education_level": str, "occupation": str, "family_occupation": str,
 "annual_family_income_inr": int, "caste_category": "SC"|"ST"|"OBC"|"EBC"|"General"}"""

TOOLS = [{
    "type": "function",
    "function": {
        "name": "search_schemes",
        "description": "Search government schemes matching a person's profile.",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {"type": "string"},
                "category": {"type": "string", "description": "e.g. scholarship, pension, health"},
            },
            "required": ["state", "category"],
        },
    },
}]


def timed(fn):
    start = time.perf_counter()
    result = fn()
    return result, time.perf_counter() - start


def test_every_model() -> None:
    print("\n1) Basic reply from each model")
    for name in MODELS:
        try:
            reply, seconds = timed(lambda: chat(name, [
                {"role": "user", "content": "In one short sentence: what is a government scholarship?"},
            ], max_tokens=400))
            print(f"   {name:10} {seconds:5.1f}s  {reply[:110]!r}")
        except Exception as error:
            print(f"   {name:10} FAILED  {error}")


def test_hinglish_profile() -> None:
    print("\n2) Hinglish -> profile JSON (Nano)")
    profile, seconds = timed(lambda: chat_json("nano", [
        {"role": "system", "content": PROFILE_PROMPT},
        {"role": "user", "content": HINGLISH_INPUT},
    ], max_tokens=1500))
    print(f"   {seconds:.1f}s")
    print("   " + json.dumps(profile, ensure_ascii=False))


def test_tool_calling() -> None:
    print("\n3) Tool calling (Super)")
    response, seconds = timed(lambda: complete("super", [
        {"role": "user", "content": HINGLISH_INPUT + " Mere liye scholarship dhoondo."},
    ], tools=TOOLS, tool_choice="auto", max_tokens=1500))
    calls = response.choices[0].message.tool_calls or []
    print(f"   {seconds:.1f}s, {len(calls)} tool call(s)")
    for call in calls:
        print(f"   -> {call.function.name}({call.function.arguments})")
    usage = response.usage
    if usage:
        print(f"   tokens: {usage.prompt_tokens} in / {usage.completion_tokens} out")


if __name__ == "__main__":
    test_every_model()
    test_hinglish_profile()
    test_tool_calling()
