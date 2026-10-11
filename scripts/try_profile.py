"""Simulate the profile conversation against the real API (calls Nemotron Nano).

Run from the project root:
    python -m scripts.try_profile

Each persona sends a first message, then answers follow-up questions from a script,
exactly the way the React app will.
"""
import json
import time

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

PERSONAS = [
    {
        "name": "Priya (Bihar student)",
        "country": "IN",
        "messages": [
            "Main Bihar se hoon, 20 saal ki hoon, BA second year mein padh rahi hoon. "
            "Papa kisan hain. Mujhe college fees ke liye madad chahiye.",
            "Ghar ki income saal ki 1.5 lakh hai, hum OBC hain",
        ],
    },
    {
        "name": "Ramesh (UP farmer, very short message, includes an Aadhaar number)",
        "country": "IN",
        "messages": [
            "main kisan hoon UP se, mera aadhaar 1234 5678 9012 hai, koi yojana batao",
            "58 saal, purush",
            "income 80 hazaar saal ki, general category",
        ],
    },
    {
        "name": "Sarah (UK single mother)",
        "country": "UK",
        "messages": [
            "I'm a single mum of two in Leeds, I work part time in a shop and I'm struggling with rent.",
            "I'm 31 and I earn about 900 pounds a month",
            "I have about 500 pounds saved, no disability",
        ],
    },
]


def run(persona: dict) -> None:
    print(f"\n=== {persona['name']} ===")
    state = {"country": persona["country"], "profile": {}, "asked": [], "answering": [], "rounds": 0, "language": None}
    for message in persona["messages"]:
        print(f"\nUSER: {message}")
        start = time.perf_counter()
        response = client.post("/api/profile", json={**state, "message": message})
        seconds = time.perf_counter() - start
        response.raise_for_status()
        reply = response.json()

        known = {k: v for k, v in reply["profile"].items() if v not in (None, [])}
        print(f"  ({seconds:.1f}s) profile: {json.dumps(known, ensure_ascii=False)}")
        if reply["privacy_note"]:
            print(f"  PRIVACY: {reply['privacy_note']}")
        if reply["follow_up"]:
            print(f"  HAQ: {reply['follow_up']['question']}  {reply['follow_up']['options']}")
        else:
            print("  HAQ: ready to show results")
            return

        # What the browser does: keep the profile, remember what was asked and the language
        state["profile"] = reply["profile"]
        state["asked"] += reply["asking"]
        state["answering"] = reply["asking"]
        state["language"] = reply["language"]
        state["rounds"] += 1


if __name__ == "__main__":
    for persona in PERSONAS:
        run(persona)
