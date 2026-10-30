# Submission form — copy-paste text

Deadline: **Oct 30, 2026, 10:30 PM IST**. Fill the form yourself; the text below is ready to paste.

## Basics

| Field | Value |
|---|---|
| Project name | **Haq** (हक़ — "what's rightfully yours") |
| Track | **Best Apps & Agents** |
| Live demo | https://haq-alpha.vercel.app |
| API (optional field) | https://haq-api.onrender.com/docs |
| Repository | https://github.com/shivanshuJags/haq (public, MIT) |
| Video | https://youtu.be/QRJ4wIwsSAU |
| City | _only if you attended a Builders & Brews event_ |

## Tagline (one line)

An AI caseworker that finds the government benefits you're entitled to, explains why in your language, and drafts your appeal when you're rejected — powered by NVIDIA Nemotron on Nebius Token Factory.

## Short description (~60 words)

Billions in benefits go unclaimed because eligibility rules are written for lawyers. Haq lets people describe
their life in their own words — English, Hinglish, Hindi, Marathi or Bengali — and checks 977 official UK and
Indian schemes. Nemotron Ultra explains every requirement, lists documents and next steps, and Rejection Rescue
turns a rejection letter into a ready-to-send appeal.

## Full description

**Problem.** Government benefits reach the people who can navigate them, not the people who need them most.
India lists thousands of central and state schemes; the UK has dozens of overlapping benefits. Official
eligibility text is long and legalistic, and a single rejection letter makes many people give up.

**What Haq does.**
- **Talk, don't fill forms.** Pick a country, state and language, then describe yourself in your own words.
  Haq asks at most three short follow-up questions, with tap-to-answer buttons.
- **Grounded understanding.** Nemotron 3 Nano extracts facts in ~2 s — and every fact must quote the user's own
  words. Code verifies the quote, checks the quote actually states the fact (no gender guessed from "student"),
  and does all arithmetic ("dedh lakh", "15 hazaar mahina", "2 bigha"), so nothing is invented.
- **Eligibility you can trust.** A rules engine filters ~1,000 schemes in milliseconds; Nemotron 3 Ultra then
  reads the official text of the best 20 in parallel and returns a structured verdict per scheme: every
  requirement as met / not met / unknown in plain language, the yearly amount only when the text states it,
  documents, how to apply, the official source — and for "almost eligible" schemes, the one next step.
  Results stream in as Ultra finishes each scheme.
- **One document checklist** across all matching schemes, to copy or download.
- **Rejection Rescue.** Paste or photograph a rejection letter: Haq reads it (vision model), finds the scheme,
  checks each reason against the official rules, recommends reapply vs appeal, computes the deadline and
  drafts a formal appeal (e.g. a UK Mandatory Reconsideration letter).
- **Built for real users:** 5 languages, installable PWA, works on small phones, ID numbers (Aadhaar, PAN,
  National Insurance) removed before any model sees them, no accounts and no user database.

**How NVIDIA Nemotron is used (all via Nebius Token Factory).**
- **Nemotron 3 Nano** — chat understanding, thinking off + strict JSON schema for speed (~2 s per message).
- **Nemotron 3 Super** — offline: extracted structured eligibility rules from 976 official scheme pages
  (0 failures, 92.8% agreement with myScheme's human tags).
- **Nemotron 3 Ultra** — eligibility judge and explainer (20 parallel calls, ~12–16 s for a full result),
  and Rejection Rescue analysis + appeal letters.
- Supporting models on Token Factory: Qwen3-Embedding-8B (semantic search), Gemma 3 27B (reading letter photos).

**Data.** GOV.UK Content API (86 UK benefits) and myScheme.gov.in (Uttar Pradesh, Bihar and 729 central
schemes), snapshotted with embeddings so the API needs no database at runtime.

**Stack.** Python 3.13 + FastAPI (Render, Docker), React 19 + TypeScript + Tailwind (Vercel, PWA), NumPy
in-memory vector search, Neon pgvector for the data pipeline. 74 automated tests.

**What we learned / challenges.** Fast small models without reasoning are great for UX but will confidently
invent facts and do arithmetic wrong — "quote your evidence, let code do the maths" fixed it without losing
speed. Ultra was accurate on long legal text but needed rules for "money that starts at 60 isn't income
today" and "a student hostel isn't for a labourer even if the list doesn't say student".

**What's next.** More Indian states and countries (config-driven), voice input, Tamil/Telugu once quality is
good enough, and partnering with legal-aid NGOs for Rejection Rescue.

## Feedback on Nebius Token Factory & NVIDIA models

See `docs/feedback.md` for the full notes. Short version for the form:

**Token Factory — liked:** OpenAI-compatible (only `base_url` changed), all three Nemotron 3 sizes in one place,
`/v1/models` for discovery, strict `json_schema` structured output, multimodal `image_url` worked out of the box,
low latency (Ultra ~1–2 s per scheme, 20 in parallel).
**Token Factory — suggestions:** add an NVIDIA embedding model and a Nemotron vision model so a pipeline can stay
all-NVIDIA; document the thinking switch (`chat_template_kwargs.enable_thinking`) on the model cards —
`reasoning_effort` and `/no_think` did not turn reasoning off, and reasoning tokens silently consume `max_tokens`
(empty answers).
**Nemotron — liked:** Nano + no-thinking + JSON schema is a superb fast extractor; Super extracted rules from 976
pages with zero failures; Ultra handled subtle legal conditions and wrote correct appeal letters.
**Nemotron — issues:** Nano (no thinking) invents plausible facts and gets spoken numbers wrong ("dedh lakh" → 1,
monthly amounts as yearly), sometimes returns nothing for a clear message; Ultra verdicts vary between identical
runs (we cache per profile); Tamil and Telugu output was not reliable enough to ship.
