# Demo video script — Haq (target 2:45, hard limit 3:00)

Voice-over in **English** (judges are global); the app itself is shown in Hinglish / Hindi.
Record the screen at phone size, then cut out every wait in the editor — the story matters, not the spinner.

## Before you record (10 minutes before)

1. **Wake the backend:** open https://haq-alpha.vercel.app and https://haq-api.onrender.com/api/health once,
   2 minutes before recording (Render's free tier sleeps after 15 minutes; the first answer takes ~20 s).
2. **Phone-size browser:** Chrome → F12 → device toolbar (Ctrl+Shift+M) → *iPhone 12 Pro* (390×844), zoom 100%.
   Or record your real phone (Android: built-in screen recorder; then copy the file to the PC).
3. **Recorder:** Windows *Xbox Game Bar* (Win+Alt+R) or OBS. **Editor:** Clipchamp (comes with Windows 11).
4. Keep the three messages below in Notepad to paste — no typos on camera.
5. Close notifications. Use an incognito window so no old state shows.

## Messages to paste

**A — India, Hinglish (student, Bihar)**
```
Main 20 saal ki student hoon, BA kar rahi hoon. Ghar ki income dedh lakh hai. College fees ke liye madad chahiye.
```
Then tap **OBC**.

**B — India, Hindi (farmer, Uttar Pradesh)**
```
मैं 62 साल का किसान हूँ, उत्तर प्रदेश के गाँव में रहता हूँ। 2 बीघा ज़मीन है, महीने के 5 हज़ार कमाता हूँ।
```
Tap **सामान्य** (General) if asked for category, **छोड़ें** (Skip) for anything else.

**C — UK (single mum)**
```
I'm 31, a single mum of two, I work part time earning about £900 a month, £500 in savings and I'm struggling with rent.
```
Tap **No** / **Skip** for the follow-ups.

## Shot list

| Time | Screen | Voice-over |
|---|---|---|
| **0:00–0:15** | Welcome screen (India, Hinglish) | "Every year, billions in government benefits go unclaimed. Not because people don't qualify — because the rules are written for lawyers, and one rejection letter makes people give up. Meet **Haq** — Hindi for *what's rightfully yours*." |
| **0:15–0:35** | Pick **Bihar ★**, tap the language chips (हिंदी → मराठी → বাংলা → back to Hinglish), scroll: counts, categories, popular, recently launched | "Haq works for the UK and India — 977 official schemes. Pick your country, state and language: English, Hinglish, Hindi, Marathi or Bengali. Countries and languages live in one config file, so adding more is easy." |
| **0:35–0:55** | Tap **Meri yojanayein dhoondho**, paste message **A**. Show the chips filling in, then the one follow-up question, tap **OBC** | "No forms. You just talk. **Nemotron Nano** turns the message into facts in about two seconds — and every fact must quote the user's own words, so nothing is invented. 'Dedh lakh' becomes ₹1.5 lakh — the maths is done in code, not by the model. It only asks what's missing." |
| **0:55–1:25** | Results stream in: total, "You likely qualify", open one card → ✓ reasons, documents, how to apply; scroll to the **document checklist** and **One step away** with *Next step* | "A rules engine checks all schemes in milliseconds; then **Nemotron Ultra** reads the official text of the best twenty, in parallel, and explains every requirement — in her language. She gets one combined document checklist, and schemes she's one step away from, with the exact next step." |
| **1:25–1:45** | ← back, switch to **हिंदी**, **Uttar Pradesh**, paste message **B** → results with **PM-KISAN ₹6,000** on top | "Same engine, in Hindi, for a 62-year-old farmer in Uttar Pradesh: 'two bigha' becomes 1.2 acres, and PM-KISAN comes out on top." |
| **1:45–2:15** | ← back → **Rejection letter mila?** → **Sample letter try karein** → **Mera letter check karo** → result: reasons ✗ fixable, deadline, then scroll the **appeal letter**, tap Copy | "Already rejected? **Rejection Rescue.** Paste the letter or snap a photo. Haq finds the scheme, checks each reason against the official rules, says whether to fix and reapply or appeal, works out the deadline — and drafts a formal appeal letter, ready to send." |
| **2:15–2:30** | ← back → **United Kingdom** → paste **C** → results (Universal Credit, Council Tax Reduction, Child Benefit) | "And in the UK, a single mum earning £900 a month finds Universal Credit, Council Tax Reduction and Child Benefit." |
| **2:30–2:50** | README on GitHub: scroll to the **architecture diagram** | "Under the hood, all reasoning runs on **NVIDIA Nemotron 3 via Nebius Token Factory**: Nano for fast, grounded chat; Super extracted eligibility rules from a thousand official pages; Ultra judges eligibility and writes appeals. ID numbers are removed before any model sees them, and there's no account and no database of users." |
| **2:50–3:00** | Back to the app (welcome screen) with the URL visible | "Haq. Open source, installable on any phone, live now at haq-alpha.vercel.app. Because what's yours should reach you." |

## After recording

1. Cut waits; keep total **under 3:00** (aim 2:45).
2. Upload to **YouTube**, visibility **Public** (or *Unlisted* only if the rules allow it), title:
   *Haq — AI caseworker for government benefits (NVIDIA Nemotron on Nebius Token Factory)*.
3. Send me the link: I'll add it to the README with 2–3 screenshots (take them from the recording: welcome
   screen, results with the checklist, Rejection Rescue letter).
