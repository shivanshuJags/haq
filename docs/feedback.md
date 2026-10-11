# Feedback notes — Nebius Token Factory & NVIDIA Nemotron

Running notes for the hackathon feedback section (US-803). Add to this as we build.

## Nebius Token Factory

**What worked well**
- OpenAI-compatible API: the official `openai` Python SDK worked by only changing `base_url` — zero custom code.
- `GET /v1/models` lists all available models, which made discovering exact model IDs easy.
- Low latency on first tests (Oct 11): Super and Ultra answered a short question in under 1 second.
- Tool calling worked out of the box with Nemotron Super (standard OpenAI `tools` format).

**Friction / suggestions**
- No NVIDIA embedding model in the catalogue at the time of testing — we used `Qwen/Qwen3-Embedding-8B` for vector search.
- No NVIDIA vision model — for reading rejection-letter photos we need a non-NVIDIA vision model.

## NVIDIA Nemotron

**Nemotron 3 Nano**
- Extracted a correct structured profile (age, gender, state, student, income, caste) from a Hinglish sentence in ~1.8s, including inferring gender from Hindi grammar ("20 saal ki hoon").

**Nemotron 3 Super**
- Correct tool call from a Hinglish request: `search_schemes({"state": "Bihar", "category": "scholarship"})`.

**Nemotron 3 Ultra**
- (to be filled when we use it for eligibility reasoning)

**Nemotron 3.5 Lightning**
- Available; slower than Super/Ultra on our first single test (2.8s). Re-check with more samples.
