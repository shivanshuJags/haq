"""Conversation languages: one place to add a language.

Each language needs: an instruction telling the models how to write it, and (in
core/profile_agent.py) the follow-up question templates + quick-reply buttons.

Tested Oct 2026 with Nemotron 3 (Nano extraction + Ultra writing):
  hindi    — understood 6/6 facts, writes correctly
  marathi  — 4/6 facts (misses some, asked as follow-ups), writes well
  bengali  — 5/6 facts, writes well
  tamil    — NOT enabled: extraction produced wrong facts (state, social category)
  telugu   — NOT enabled: written answers mixed scripts and leaked instructions
"""
from typing import Literal

Language = Literal["english", "hinglish", "hindi", "marathi", "bengali"]

INSTRUCTIONS: dict[str, str] = {
    "english": "simple English",
    "hinglish": "Hinglish (Hindi written in Latin script, like 'Aapki umar kitni hai?')",
    "hindi": "Hindi in Devanagari script (हिंदी), simple everyday words",
    "marathi": "Marathi in Devanagari script (मराठी), simple everyday words",
    "bengali": "Bengali in Bengali script (বাংলা), simple everyday words",
}

# Languages each country offers (the first is the default)
BY_COUNTRY: dict[str, list[str]] = {
    "IN": ["hinglish", "english", "hindi", "marathi", "bengali"],
    "UK": ["english"],
}

# Indian-script digits -> ASCII, so "२० साल" or "১.৫ লাখ" are read like "20 saal" / "1.5 lakh"
_DIGITS = {}
for zero in ("०", "০", "௦", "౦", "੦", "૦"):  # Devanagari, Bengali, Tamil, Telugu, Gurmukhi, Gujarati
    base = ord(zero)
    for value in range(10):
        _DIGITS[chr(base + value)] = str(value)
DIGIT_TABLE = str.maketrans(_DIGITS)


def ascii_digits(text: str) -> str:
    return text.translate(DIGIT_TABLE)
