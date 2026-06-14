# PharmaOps — ONE Simple Demo Order (read this only)

You were confused because we mixed **3 different things**. Here is the truth.

---

## The 3 things (what each one IS)

| Thing | What it is | Show in video? |
|-------|------------|----------------|
| **Splunk dashboard** | Where manufacturing data lives (like a database) | Yes — 20 seconds, proof data is real |
| **Streamlit app** | **YOUR APP** — what plant managers use | **YES — main demo** |
| **HTML report file** | Report saved to disk | **No separate window** — Streamlit shows it inside the app |

**Splunk = engine. Streamlit = car. HTML = receipt saved in the glove box.**

You don't show the receipt from the glove box before showing the car.  
You drive the car (Streamlit). Splunk is under the hood.

---

## WRONG order (what confused you)

```
Splunk → Terminal command → HTML pops open in browser ❌
```

That was a **developer shortcut** (`--open-report`). Judges don't need it.

---

## RIGHT order (use this for video + Ignite64)

### Step 1 — Start Streamlit (your app)

```bash
cd /Users/prakashrajk/pharmaops-monitor
source .venv/bin/activate
export GEMINI_API_KEY=your_real_key
./run_streamlit.sh
```

Open: **http://localhost:8501**

---

### Step 2 — Tab: Dashboard (10 sec)

- Show the overview image
- Click **"Open Live Splunk Dashboard"** button
- Splunk opens → point at BATCH-1027, **24** deviations
- **Go back to Streamlit** (this is your home base)

**Say:** "Data lives in Splunk. Plant managers work in PharmaOps."

---

### Step 3 — Tab: Multi-Agent (main demo ⭐)

- Click **"Run Multi-Agent Pipeline"**
- Wait ~1–2 min
- Report appears **inside Streamlit** (not a new browser tab)

**Say:** "Three AI agents detect, investigate, and QA-review — report generated here."

---

### Step 4 — Tab: Regulatory

- Click **"Generate Regulatory Report"**
- GMP score, QMS risk, PV — all **inside the app**
- HTML embeds at bottom of same tab

---

### Step 5 — Tab: Ask AI

- Type: `What batches failed and why?`
- Click **Ask**
- Answer appears in app

---

### Step 6 — Tab: Reports (optional)

- Shows saved HTML reports **embedded in Streamlit**
- Proves reports are stored, not lost

---

## What you do NOT need for demo

| Skip this | Why |
|-----------|-----|
| `python3 agent/pharma_agent.py --multi-agent --open-report` | Opens HTML in separate tab — confuses the story |
| `./scripts/run_end_to_end.sh` | Developer test script, not judge demo |
| Opening HTML files manually | Streamlit already shows them |

---

## 30-second pitch while using Streamlit

> "Splunk ingests factory data. PharmaOps is the command center on top — AI agents investigate deviations and generate FDA reports. One app, one click, under three minutes."

---

## Quick reference

```
START  → ./run_streamlit.sh
HOME   → http://localhost:8501
PROOF  → Dashboard tab → Open Splunk (20 sec)
MAGIC  → Multi-Agent tab → Run button
CHAT   → Ask AI tab
DONE   → close with Regulatory tab scores
```

**Streamlit first. Splunk second. Never open HTML separately.**
