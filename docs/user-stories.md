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

### US-104 · Structured eligibility rules · P0 · Done (demo review pending)
**As a** developer, **I want** each scheme's eligibility text turned into structured rules, **so that** hard criteria can be checked in code, not guessed by AI.
- [x] Rule schema defined (age, income, state, gender, category, occupation, student, disability, etc.) — `core/rules.py`
- [x] Nemotron Super extracts rules from eligibility text into that schema — `ingest/extract_rules.py`, 976/976, 0 failed
- [x] Unclear criteria are kept as free text (`other_conditions`) instead of being invented
- [x] Hard rules never wrongly exclude: OR-lists → `other_conditions`, loosest limit when it varies by group, `false` only when explicitly excluded, `sanitize()` cleanup
- [x] Cross-check India rules against myScheme's own search filters — `ingest/india_tags.py` + `scripts/compare_rules.py`: 92.8% agreement; sampled conflicts were mostly missing myScheme tags, not Nemotron errors
- [x] Ayushman Bharat PM-JAY added by hand — `data/manual/india.json` (**verify on pmjay.gov.in before demo**)
- [x] Rules saved alongside each scheme — `data/processed/rules.json`
- [ ] Manual review of the ~30 schemes used in the demo — do on Oct 23–24 once demo personas' results are known

### US-105 · Database and search · P0 · Done
**As a** developer, **I want** schemes stored in PostgreSQL with vector search, **so that** the agent can find relevant schemes quickly.
- [x] Tables for schemes and rules — `db/schema.sql` on Neon (single `schemes` table, rules as jsonb)
- [x] Embeddings stored with pgvector — Qwen3-Embedding-8B @ 1024 dims, HNSW cosine index
- [x] Load script imports `data/processed/*.json` + `data/manual/` — `db/load.py` (upsert, removes stale, embeds only changed)
- [x] Search by meaning works in Hinglish and English — `core/search.py`, `scripts/try_search.py`

**Finding:** a vague query ("padhai ke liye paise") ranks the 729 central schemes above state ones; Bihar's Post-Matric Scholarship wasn't in the top 40. With the full profile in the query it rose to #9 and the top result was the right OBC scholarship. → see US-301 design.

### US-106 · Weekly data refresh · P1 · To do · Oct 27
**As a** user, **I want** scheme data to stay current, **so that** I don't act on outdated rules.
- [ ] Ingestion runs as a Nebius Serverless Job
- [ ] Each scheme shows "last updated" date

---

## Epic 2 — Eligibility conversation

### US-201 · Describe my situation in plain words · P0 · Backend done · Oct 17–19
**As** Priya, **I want** to describe my life in my own words (English or Hinglish), **so that** I don't have to fill a long form.
- [x] API: `POST /api/profile` accepts a free-text message — `api/routes/profile.py`
- [x] Nemotron Nano extracts a profile (age, state, income, category, occupation, student, gender, disability, family details) — `core/profile.py`, `core/profile_agent.py`
- [x] Short answers map to the field we just asked about (`answering`)
- [x] Frontend: free-text chat input (US-701)
- [x] Frontend: extracted profile shown back as chips; × removes a wrong fact so Haq can ask again
- [x] "single mum" no longer becomes "unmarried" (code check after Nano)

### US-202 · Follow-up questions · P0 · Backend done · Oct 17–19
**As** Ramesh, **I want** Haq to ask me only what's missing, **so that** results are accurate without a long questionnaire.
- [x] At most 3 rounds, max 2 facts per question, never asks the same thing twice
- [x] Questions in the user's language — decided in code (`detect_language`), kept across short answers
- [x] Quick-reply options for choices (category, gender)
- [x] Fast: Nano with thinking off + structured JSON output (~0.5–1.5s)
- [x] Frontend: user can skip a question
- [x] Situational questions: farmers are asked about land (PM-Kisan needs land in their name)
- [ ] Polish: Hinglish wording is sometimes clumsy ("parivaar ki poora samasya ki income")

### US-203 · Privacy by default · P0 · Backend done · Oct 17–19
**As** a user, **I want** my personal details not stored, **so that** I feel safe sharing them.
- [x] Stateless API: the browser holds the profile, the server stores nothing
- [x] Aadhaar / PAN / NI / account numbers are removed before the text reaches the model — `core/privacy.py` (+ tests)
- [x] Privacy note returned in the user's language when a number was removed
- [x] Frontend: privacy note visible in the chat (always, plus 🔒 note when a number was removed)

---

## Epic 3 — Results

### US-301 · See schemes I'm eligible for · P0 · Backend done
**As** Sarah, **I want** a list of benefits I qualify for, **so that** I know what to claim.
- [x] Candidates = every scheme for the person's country/state that passes the hard rules — `core/eligibility.py` (pass/fail/unknown, "fail only when sure", 10 tests), `core/candidates.py`
- [x] Rank by vector similarity to a query built from the FULL profile; 15 best + 5 reserved state slots
- [x] Shortlist judged by Nemotron Ultra in parallel (20 at once) — `core/verdict.py`: verdict (eligible / likely / need_more_info / not_eligible) + fit (strong / possible / weak)
- [x] Result cards with benefit line + yearly cash amount (only real cash; not insurance cover or loans) — `core/results.py`, `POST /api/results`
- [x] Sorted by verdict, then relevance; weak matches in a separate `other_cards` list
- [x] Totals: `total_yearly` (eligible + likely) and `potential_yearly` (+ need more info)
- [x] Fast enough: DB connection pool + in-memory catalog (`core/db.py`, `core/catalog.py`) — candidates ~1.5s warm; Ultra ~8–15s
- [x] Frontend: cards, totals, progress while Ultra works (US-701)
- [ ] Known: Ultra's verdict can vary between runs (likely ↔ need_more_info), which changes the total. Consider temperature/consistency check before demo

### US-302 · Why am I eligible? · P0 · Backend done
**As** Priya, **I want** to see why I qualify, **so that** I can trust the result.
- [x] Each card has 2–5 reasons with met / not_met / unknown, in the user's language
- [x] `to_confirm`: what the person should check or provide
- [x] Link to the official source page on every card (`source_url`)
- [x] Frontend: show ✓ / ✗ / ? list

### US-303 · What documents do I need? · P0 · Backend done
**As** Ramesh, **I want** a list of documents for each scheme, **so that** I carry the right papers.
- [x] Documents list on each card (cleaned of HTML entities)
- [ ] Combined, de-duplicated checklist across all eligible schemes (P1)
- [x] Frontend (links inside document names are clickable)

### US-304 · How do I apply? · P0 · Backend done
**As** Sarah, **I want** clear steps and the apply link, **so that** I can apply right away.
- [x] Application steps (`how_to_apply` markdown) + `apply_url` when available
- [x] Frontend

### US-305 · Almost eligible · P1 · To do · Oct 23–24
**As** Priya, **I want** to know which schemes I could get with one more step, **so that** I can unlock more benefits.
- [ ] Shows schemes that fail on only one fixable criterion (e.g. missing certificate)
- [ ] Says exactly what to do to become eligible

---

## Epic 4 — Countries

### US-401 · Switch country · P0 · Done
**As a** judge, **I want** to switch between UK and India, **so that** I can see the same engine working for both.
- [x] Country selector (UK / India) on the welcome screen; "Haq" logo returns to it
- [x] India asks for state (UP / Bihar / other → central schemes only)
- [x] Currency, greeting and wording change with the country

---

## Epic 5 — Rejection Rescue

### US-501 · Understand my rejection · P1 · Done
**As** Tom, **I want** to upload or paste my rejection letter, **so that** I understand why I was rejected.
- [x] Accepts pasted text or a photo (resized in the browser to ≤1600px); photo read by `google/gemma-3-27b-it` (no NVIDIA vision model on Token Factory) — `core/rescue.py`, `POST /api/rescue`
- [x] ID numbers removed before the letter is analysed; nothing stored
- [x] Finds the scheme with vector search (national + UP + Bihar candidates); Ultra picks it or says "none" instead of guessing a variant
- [x] Nemotron Ultra explains each reason simply, says if it's fixable, and checks it against the official rules (looks correct: yes / no / unclear)
- [x] Entry point on the welcome screen; fictional sample letters for India and UK (`web/src/samples.ts`)

### US-502 · Fix and appeal · P1 · Done
**As** Tom, **I want** a ready appeal letter and a fix list, **so that** I can challenge the decision.
- [x] Recommendation (re-apply / appeal / either / not eligible) + reason, deadline from the letter, documents to gather
- [x] Editable formal appeal letter with [placeholders], addressed to the office that rejected
- [x] Copy / download the letter
- [x] Verified in browser (India sample: Bihar Post-Matric Scholarship, deadline 05/10/2026, letter to District Welfare Officer Patna); UK sample (PIP) → mandatory reconsideration letter in ~9s

---

## Epic 6 — Trust and safety

### US-601 · Disclaimers and attribution · P0 · Done
**As a** user, **I want** to know this is guidance, not an official decision, **so that** I verify before applying.
- [x] "Guidance only" disclaimer visible on every screen — `web/src/components/Footer.tsx`
- [x] Footer attribution: myScheme.gov.in, GOV.UK (Open Government Licence)
- [x] Manually added schemes show "please verify on the official website"

### US-602 · No made-up answers · P0 · To do · Oct 23–24
**As a** user, **I want** answers grounded in official text, **so that** I'm not misled.
- [ ] Every claim links to a source
- [ ] If data is missing, Haq says "not sure" instead of guessing

---

## Epic 7 — App and deployment

### US-701 · Mobile-friendly web app (PWA) · P0 · In progress
**As** Ramesh, **I want** Haq to work well on my phone, **so that** I can use it without a laptop.
- [x] React app (`web/`: Vite + React + TypeScript + Tailwind), mobile-first layout
- [x] Screens: welcome (₹ India + UP/Bihar/other, £ UK) → chat → loading steps → results → error/retry
- [x] Chat: bubbles, quick replies, skip, "show my results", privacy note, removable profile chips (one swipeable row on phones)
- [x] Results: total hero (+ "up to"), scheme cards with verdict, amount, ✓/✗/? reasons, to-confirm, documents, how to apply (markdown), apply + source links, weak matches collapsed
- [x] UI follows the conversation language (English / Hinglish)
- [x] Verified in browser at 375px (Priya: Bihar Post-Matric Scholarship on top, ₹70,520/yr; Sarah: Universal Credit £12,393/yr), no horizontal overflow
- [ ] Installable as a PWA (manifest + icons + service worker)
- [ ] Polish: footer takes ~90px on phones — make it smaller / scroll with content
- [x] Latency: chat replies now ~1–4s (was 6–15s) — Nano thinking off + "grounded extraction" (`core/grounded.py`): every fact needs a quote from the message that code verifies, numbers must appear in the quote, code does all unit maths (lakh/hazaar/month/week/bigha), Hindi-grammar safety net for gender/student
- [x] Results stream (`POST /api/results/stream`, NDJSON start → card/progress → done): results page opens after the rules engine, cards appear as Ultra finishes each, live total + progress bar
- [x] One choice question at a time (gender / category / occupation) so quick-reply buttons match the question
- [x] Follow-up questions are fixed templates in both languages (no model — instant, never off-topic); income never offers ranges
- [x] Tapped quick replies are understood in code (`OPTION_VALUES`, ~0.2s); safety nets for category phrases and capitalisation
- [x] `dev.ps1` starts backend + frontend together; README "Run locally"

### US-702 · Live deployment · P0 · In progress
**As a** judge, **I want** a public demo URL, **so that** I can try Haq myself.
- [x] Backend container (`Dockerfile`, 441 MB) — tested locally: ready in ~1s, chat / results stream / Rejection Rescue all pass
- [x] No database at runtime: catalog snapshot (`db/snapshot.py` → `data/snapshot/`) shipped in the image; similarity computed in memory with numpy (Neon free tier took 10–56s to connect)
- [x] Frontend reads the API location from `VITE_API_URL`; backend CORS from `ALLOWED_ORIGINS`
- [x] Step-by-step guide: `docs/deploy.md`
- [ ] Push image to a registry (user's Docker Hub account)
- [ ] Backend on Nebius Serverless Endpoint (console; CLI is Linux/macOS only)
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
