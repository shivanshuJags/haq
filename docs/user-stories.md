# Haq — User Stories

This is the backlog we build from. Every task we pick up maps to a story ID here.
When a story is finished, tick its acceptance criteria and set its status to Done.

**Deadline:** Oct 30, 2026, 10:30 PM IST
**Status values:** To do · In progress · Done
**Priority:** P0 = MVP (must ship) · P1 = strong feature (should ship) · P2 = stretch (only if time is left)

---

## Personas

| Persona | Who they are | What they need |
|---|---|---|
| **Priya** (India) | 20, BA student in Bihar, father is a farmer, family income ₹1.5 lakh | Find scholarships and family schemes she doesn't know about |
| **Ramesh** (India) | 58, small farmer in Uttar Pradesh, not comfortable with English | Simple Hinglish answers; know which documents to carry |
| **Sarah** (UK) | 31, single mother in Leeds, works part time | Know which benefits she can claim and how much she'd get |
| **Tom** (UK) | 45, got a rejection letter for PIP | Understand why he was rejected and how to appeal |
| **Judge** | Hackathon evaluator | See a working demo, clear Nemotron usage, open-source repo |
| **Developer** (us) | Builds and maintains Haq | Reliable, refreshable data; easy setup |

---

## Epic 0 — Project foundation

### US-001 · Project setup · P0 · Done
**As a** developer, **I want** a clean project structure with a Python environment, **so that** anyone can clone and run Haq.
- [x] Folder `haq/` with `ingest/`, `data/`, `docs/`
- [x] Python virtual environment + `requirements.txt`
- [x] `.gitignore` excludes `.venv`, `.env`, raw data
- [x] MIT `LICENSE`
- [x] `README.md` with setup steps
- [ ] First git commit

### US-002 · Nebius Token Factory connection · P0 · Done
**As a** developer, **I want** to call Nemotron models from Python, **so that** every AI feature has a working base.
- [x] API key read from `.env` (never hard-coded, never committed) — `core/config.py`
- [x] Small client module that can call Nano, Super and Ultra by name — `core/llm.py`
- [x] Test script confirms: available model names, a reply from each model, tool calling works — `scripts/check_llm.py`
- [x] Hinglish test: Nano extracts correct facts from a Hinglish sentence
- [x] Note in `docs/feedback.md`: what was easy or hard in Token Factory

**Findings:** no NVIDIA embedding model → use `Qwen/Qwen3-Embedding-8B`. No NVIDIA vision model → use `google/gemma-3-27b-it` or `openbmb/MiniCPM-V-4_5` for letter photos (US-501).

---

## Epic 1 — Scheme data

### US-101 · UK benefits data · P0 · Done
**As a** developer, **I want** UK benefits downloaded from GOV.UK, **so that** the UK pack has real data.
- [x] Lists benefits from all 7 GOV.UK benefit categories
- [x] Downloads each page via the Content API (rate-limited)
- [x] Saves to the common scheme format in `data/processed/uk.json`
- [x] Links are absolute URLs
- [x] Each record has `source_url` and licence

### US-102 · India state schemes data (UP + Bihar) · P0 · Done
**As a** developer, **I want** all Uttar Pradesh and Bihar schemes from myScheme, **so that** the India pack covers our personas.
- [x] Downloads every UP and Bihar scheme (list → detail → documents) — 47 UP + 113 Bihar
- [x] ₹ characters display correctly (myScheme sends valid UTF-8; just read it as UTF-8)
- [x] Saves in the same common format as UK (`data/processed/india.json`)
- [x] Each record has `source_url` and myScheme attribution
- [x] Rate-limited; raw responses cached in `data/raw/india/` so re-runs take seconds

### US-103 · India central schemes · P0 · Done (one follow-up)
**As** Priya, **I want** central schemes (PM-Kisan, scholarships, Ayushman Bharat) included, **so that** I'm not missing the biggest benefits.
- [x] All central schemes downloaded — 729 kept (746 listed, 5 closed, 12 broken on myScheme)
- [x] `regions: null` when a scheme applies to every state; list of states when it is restricted
- [x] Closed schemes (close date in the past) skipped
- [ ] Follow-up: myScheme's own page for **Ayushman Bharat PM-JAY** is broken. Add it (and other important ones from `data/processed/india_missing.json`) by hand from the official site in US-104's manual review

### US-104 · Structured eligibility rules · P0 · To do · Oct 15–16
**As a** developer, **I want** each scheme's eligibility text turned into structured rules, **so that** hard criteria can be checked in code, not guessed by AI.
- [ ] Rule schema defined (age, income, state, gender, category, occupation, student, disability, etc.)
- [ ] Nemotron Super extracts rules from eligibility text into that schema
- [ ] Unclear criteria are kept as free text (`other_conditions`) instead of being invented
- [ ] Cross-check India rules against myScheme's own search filters (gender, age, caste, isStudent, occupation, isBpl, disability, residence) — query each filter value and record which schemes match
- [ ] Manual review of the top 30 schemes used in the demo
- [ ] Rules saved alongside each scheme

### US-105 · Database and search · P0 · To do · Oct 17
**As a** developer, **I want** schemes stored in PostgreSQL with vector search, **so that** the agent can find relevant schemes quickly.
- [ ] Tables for schemes and rules
- [ ] Embeddings stored with pgvector
- [ ] Load script imports `data/processed/*.json`

### US-106 · Weekly data refresh · P1 · To do · Oct 27
**As a** user, **I want** scheme data to stay current, **so that** I don't act on outdated rules.
- [ ] Ingestion runs as a Nebius Serverless Job
- [ ] Each scheme shows "last updated" date

---

## Epic 2 — Eligibility conversation

### US-201 · Describe my situation in plain words · P0 · To do · Oct 17–19
**As** Priya, **I want** to describe my life in my own words (English or Hinglish), **so that** I don't have to fill a long form.
- [ ] Free-text chat input
- [ ] Nemotron Nano extracts a profile (age, state, income, category, occupation, student, gender, disability, family details)
- [ ] Extracted profile shown back to the user as editable chips

### US-202 · Follow-up questions · P0 · To do · Oct 17–19
**As** Ramesh, **I want** Haq to ask me only what's missing, **so that** results are accurate without a long questionnaire.
- [ ] Asks at most 2–3 short follow-up questions
- [ ] Questions are in the user's language style
- [ ] User can skip a question

### US-203 · Privacy by default · P0 · To do · Oct 17–19
**As** a user, **I want** my personal details not stored, **so that** I feel safe sharing them.
- [ ] Profile lives only in the session
- [ ] Never asks for Aadhaar, NI number, bank details
- [ ] Privacy note visible in the chat

---

## Epic 3 — Results

### US-301 · See schemes I'm eligible for · P0 · To do · Oct 20–22
**As** Sarah, **I want** a list of benefits I qualify for, **so that** I know what to claim.
- [ ] Hard rules checked in code first, then Nemotron Ultra reasons about unclear criteria
- [ ] Result cards: name, short description, amount (₹/£ where known)
- [ ] Sorted by relevance / value
- [ ] Total estimated benefit shown at top

### US-302 · Why am I eligible? · P0 · To do · Oct 23–24
**As** Priya, **I want** to see why I qualify, **so that** I can trust the result.
- [ ] Each card lists criteria with ✓ / ✗ / ? against my profile
- [ ] Link to the official source page on every card

### US-303 · What documents do I need? · P0 · To do · Oct 20–22
**As** Ramesh, **I want** a list of documents for each scheme, **so that** I carry the right papers.
- [ ] Documents shown on each card
- [ ] Combined, de-duplicated checklist across all eligible schemes (P1)

### US-304 · How do I apply? · P0 · To do · Oct 20–22
**As** Sarah, **I want** clear steps and the apply link, **so that** I can apply right away.
- [ ] Application steps shown
- [ ] Online apply link when available; offline steps otherwise

### US-305 · Almost eligible · P1 · To do · Oct 23–24
**As** Priya, **I want** to know which schemes I could get with one more step, **so that** I can unlock more benefits.
- [ ] Shows schemes that fail on only one fixable criterion (e.g. missing certificate)
- [ ] Says exactly what to do to become eligible

---

## Epic 4 — Countries

### US-401 · Switch country · P0 · To do · Oct 20–22
**As a** judge, **I want** to switch between UK and India, **so that** I can see the same engine working for both.
- [ ] Country selector (UK / India)
- [ ] India asks for state (UP / Bihar)
- [ ] Currency, examples and wording change with the country

---

## Epic 5 — Rejection Rescue

### US-501 · Understand my rejection · P1 · To do · Oct 25–26
**As** Tom, **I want** to upload or paste my rejection letter, **so that** I understand why I was rejected.
- [ ] Accepts pasted text; image upload with OCR if a vision model is available
- [ ] Nemotron Ultra explains the reason in simple words
- [ ] Matches the reason against the scheme's rules

### US-502 · Fix and appeal · P1 · To do · Oct 25–26
**As** Tom, **I want** a ready appeal letter and a fix list, **so that** I can challenge the decision.
- [ ] Lists what to fix or which evidence to add
- [ ] Generates an editable appeal letter
- [ ] Copy / download the letter

---

## Epic 6 — Trust and safety

### US-601 · Disclaimers and attribution · P0 · To do · Oct 20–22
**As a** user, **I want** to know this is guidance, not an official decision, **so that** I verify before applying.
- [ ] "Guidance only" disclaimer visible
- [ ] Footer attribution: myScheme.gov.in, GOV.UK (Open Government Licence)

### US-602 · No made-up answers · P0 · To do · Oct 23–24
**As a** user, **I want** answers grounded in official text, **so that** I'm not misled.
- [ ] Every claim links to a source
- [ ] If data is missing, Haq says "not sure" instead of guessing

---

## Epic 7 — App and deployment

### US-701 · Mobile-friendly web app (PWA) · P0 · To do · Oct 20–22
**As** Ramesh, **I want** Haq to work well on my phone, **so that** I can use it without a laptop.
- [ ] React app, mobile-first layout
- [ ] Installable as a PWA

### US-702 · Live deployment · P0 · To do · Oct 27
**As a** judge, **I want** a public demo URL, **so that** I can try Haq myself.
- [ ] Backend on Nebius Serverless Endpoint
- [ ] Frontend on Vercel
- [ ] Demo works end to end on the live URL

---

## Epic 8 — Hackathon submission

### US-801 · Repository ready for judges · P0 · To do · Oct 28
- [ ] Public GitHub repo, MIT licence visible
- [ ] README: setup, architecture diagram, how Nemotron Nano/Super/Ultra are used, Token Factory benefits, Nebius services used
- [ ] Data attribution section

### US-802 · Demo video · P0 · To do · Oct 29
- [ ] Under 3 minutes, public on YouTube
- [ ] Shows: problem → UK demo → India switch → Rejection Rescue → architecture → close

### US-803 · Submission form · P0 · To do · Oct 30
- [ ] Track: Best Apps & Agents
- [ ] Description, demo URL, video URL, repo URL
- [ ] Feedback on Nebius Token Factory and NVIDIA models (from `docs/feedback.md`)
- [ ] City (if attended a Builders & Brews event)
- [ ] Submitted before 10:30 PM IST

---

## Epic 9 — Stretch

### US-901 · Hindi answers · P2 · To do
### US-902 · Voice input · P2 · To do
### US-903 · Download my results as PDF · P2 · To do
