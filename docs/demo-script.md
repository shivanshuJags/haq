# Demo video script — Haq (target 2:45, hard limit 3:00)

Voice-over in **English** (judges are global); the app is shown in Hinglish, Hindi and English.
Speak slowly: ~400 words of voice-over = ~2:45. Cut every wait (spinners) in the editor.

## Setup (15 minutes before)

1. **Wake the backend:** open https://haq-api.onrender.com/api/health → wait for `{"status":"ok"...}`.
   Then open https://haq-alpha.vercel.app once and do one quick chat (Render sleeps after 15 min).
2. **Browser:** Chrome **Incognito** (Ctrl+Shift+N) → open https://haq-alpha.vercel.app →
   F12 → device toolbar (Ctrl+Shift+M) → **iPhone 12 Pro**, zoom **100%**. Undock DevTools to a separate window
   (⋮ → Dock side → separate) so only the phone shows. Browser zoom (Ctrl +) so the phone fills the screen height.
3. **Recorder:** Xbox Game Bar (**Win+Alt+R** start/stop) or OBS. **Editor:** Clipchamp (built into Windows 11).
4. Notifications off (Focus / Do not disturb). Close other tabs.
5. Open Notepad with the 3 messages below — copy-paste, never type on camera.
6. Second tab ready: https://github.com/shivanshuJags/haq (scrolled to the *Architecture* diagram).

**Easiest way:** record the screen **without voice** first (scene by scene), then record the voice-over
separately in Clipchamp (Record → Audio) while watching the clip, and trim the video to match your voice.

## Messages to paste

**A — Hinglish, Bihar student**
```
Main 20 saal ki student hoon, BA kar rahi hoon. Ghar ki income dedh lakh hai. College fees ke liye madad chahiye.
```

**B — Hindi, UP farmer**
```
मैं 62 साल का किसान हूँ, उत्तर प्रदेश के गाँव में रहता हूँ। 2 बीघा ज़मीन है, महीने के 5 हज़ार कमाता हूँ।
```

**C — UK single mum**
```
I'm 31, a single mum of two, I work part time earning about £900 a month, £500 in savings and I'm struggling with rent.
```

---

## Scene by scene

### Scene 1 — Hook (0:00–0:15)
**Screen:** Welcome screen, India selected, Hinglish. Don't touch anything — just hold still (or move the mouse slowly over the title).

**Say:**
> "Every year, billions in government benefits go unclaimed. Not because people don't qualify — but because the rules are written for lawyers, and one rejection letter makes people give up. Meet Haq — Hindi for *what's rightfully yours*."

### Scene 2 — Welcome screen (0:15–0:35)
**Do:**
1. Country = **India**. State dropdown → pick **Bihar ★**.
2. Tap language chips one by one: **हिंदी** → **मराठी** → **বাংলা** → back to **Hinglish** (≈1 s each, the screen changes language).
3. Scroll down slowly: scheme count → **Category se dekhein** tiles → **Lokpriya yojanayein** → **Haal mein shuru hui**.
4. Scroll back up.

**Say:**
> "Haq covers the UK and India — nine hundred and seventy-seven official schemes. Pick your country, your state and your language: English, Hinglish, Hindi, Marathi or Bengali. You can also browse categories, popular schemes, and newly launched ones."

### Scene 3 — Chat (0:35–0:55)
**Do:**
1. Tap **Meri yojanayein dhoondho**.
2. Paste message **A** → tap **Bhejein**.
3. Let the profile chips appear on top (age 20, Bihar, student, ₹1,50,000…). Hover the income chip for a second.
4. Haq asks for category → tap **OBC**.
5. If it asks anything else → tap **Chhodein**. When the button appears → tap **Mere results dikhao**.

**Say:**
> "No forms — you just talk. Nemotron Nano turns the message into facts in about two seconds, and every fact must quote the user's own words, so nothing is invented. 'Dedh lakh' becomes one and a half lakh rupees, because the maths is done in code, not by the model. Then it asks only what's missing."

### Scene 4 — Results (0:55–1:25)
**Do:**
1. Results stream in (cut the waiting in the editor). Show the yearly total at the top.
2. Tap the **first scheme card** to open it → slowly show ✓ reasons → documents → how to apply → **Official page** link.
3. Close it, scroll down to **Aapke documents ki checklist** → tap **List copy karein**.
4. Scroll to the "Ye bhi mil sakti hain" section → show one **Agla kadam** line.

**Say:**
> "A rules engine checks every scheme in milliseconds. Then Nemotron Ultra reads the official text of the best twenty, in parallel, and explains each requirement — in her own language. She gets one combined document checklist, and the schemes she's one step away from, with the exact next step."

### Scene 5 — Hindi farmer (1:25–1:45)
**Do:**
1. Tap **Wapas** (back) → welcome screen.
2. Language **हिंदी**, state **Uttar Pradesh ★**.
3. Tap the find button → paste message **B** → send.
4. Category question → tap **सामान्य**; anything else → **छोड़ें**; then show results.
5. Show **PM-KISAN ₹6,000** near the top.

**Say:**
> "The same engine works in Hindi — for a sixty-two-year-old farmer in Uttar Pradesh. 'Two bigha' becomes one point two acres, and PM-KISAN comes out on top."

### Scene 6 — Rejection Rescue (1:45–2:15)
**Do:**
1. Back → welcome screen (Hinglish again is fine).
2. Tap **Rejection letter mila?**
3. Tap **Sample letter try karein** (the letter text fills in) → tap **Mera letter check karo**.
4. Cut the wait. Show: the scheme it found → each reason (✗ / fixable) → reapply-or-appeal advice → **deadline**.
5. Scroll to **Aapka appeal letter** → slowly scroll through the letter → tap **Copy**.

**Say:**
> "Already rejected? Rejection Rescue. Paste the letter, or snap a photo. Haq finds the scheme, checks each reason against the official rules, says whether to fix and reapply or appeal, works out the deadline — and drafts a formal appeal letter, ready to send."

### Scene 7 — UK (2:15–2:30)
**Do:**
1. Back → country **United Kingdom** (language becomes English).
2. Tap the find button → paste message **C** → send. Follow-ups → **No** / **Skip** → show results.
3. Show **Universal Credit**, **Council Tax Reduction**, **Child Benefit**.

**Say:**
> "And in the UK, a single mum earning nine hundred pounds a month finds Universal Credit, Council Tax Reduction, Child Benefit and more."

### Scene 8 — Architecture (2:30–2:50)
**Do:** Switch to the GitHub tab (exit phone mode is fine here) → README → scroll slowly through the **Nemotron model table** and the **Architecture** diagram.

**Say:**
> "Under the hood, all reasoning runs on NVIDIA Nemotron 3, through Nebius Token Factory. Nano for fast, grounded chat. Super extracted eligibility rules from almost a thousand official pages. Ultra judges eligibility and writes the appeals. ID numbers are removed before any model sees them, and there are no accounts."

### Scene 9 — Close (2:50–3:00)
**Do:** Back to the app's welcome screen with the URL bar visible (haq-alpha.vercel.app).

**Say:**
> "Haq is open source, installs on any phone, and is live now at haq-alpha.vercel.app. Because what's yours should reach you."

---

## Editing in Clipchamp

1. Import the screen recordings → drag to the timeline in scene order.
2. **Split (S)** and delete every spinner / waiting part — results should appear to load in 1–2 s.
3. Record the voice-over: **Record & create → Audio** (or record on your phone and import). One scene per take.
4. Line up each voice clip with its scene; trim or speed up (1.25×) video parts that run longer than the voice.
5. Optional: add a text box at the start ("Haq — AI caseworker for government benefits") and at the end (the live URL + GitHub URL).
6. Check total length **under 3:00** → Export **1080p**.

## Upload

1. YouTube → Create → Upload video → visibility **Public**.
2. Title: *Haq — AI caseworker for government benefits (NVIDIA Nemotron on Nebius Token Factory)*.
3. Description: the first two lines of `docs/submission.md` + the live link + the GitHub link.
4. Put the YouTube link in README (`🎬 Demo video` row) and in the submission form.

## If something goes wrong while recording

- **First answer is slow / error:** the backend was asleep — wait 30 s, tap **Wapas**, try again (cut it out later).
- **A different scheme shows on top:** fine — Ultra's ranking can vary a little; just narrate what is on screen.
- **Haq asks an extra question:** tap **Chhodein** / **Skip**.
