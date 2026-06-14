# Record PharmaOps Video — Streamlit Demo (3 min)

**Use this script only.** Streamlit = your app. Splunk = 20 sec proof. No terminal. No separate HTML.

---

## BEFORE YOU RECORD (10 min)

### 1. Start everything

```bash
cd /Users/prakashrajk/pharmaops-monitor
source .venv/bin/activate
export GEMINI_API_KEY=your_real_key_here
./run_streamlit.sh
```

Browser opens → **http://localhost:8501**  
Keep that terminal open.

### 2. Check Splunk is running (for 20-sec proof later)

Open in a second tab (don't record yet):
http://localhost:8000/en-US/app/search/pharmaops_monitor  
Time range: **All time**

### 3. Recording setup

- Mac → **QuickTime** → File → New Screen Recording
- Close Slack, notifications, extra tabs
- Zoom browser to readable size
- Rehearse opening line once

### 4. Quick test (not recorded)

In Streamlit → **Multi-Agent** tab → click **Run Multi-Agent Pipeline** once.  
If it finishes with a report → you're ready.

---

## PRESS RECORD

---

### SCENE 1 — HOOK (0:00 – 0:25)

**SHOW:** Streamlit home — PharmaOps Monitor header visible

**SAY:**
> "Indian pharma loses fifty lakh to one crore rupees when a single batch fails. Plant managers spend hours digging through logs. PharmaOps Monitor is an AI command center that detects, investigates, and reports GMP deviations in under three minutes."

---

### SCENE 2 — SPLUNK PROOF (0:25 – 0:50)

**SHOW:** Click **Dashboard** tab → click **"Open Live Splunk Dashboard"**

**SHOW:** Splunk — point at deviations table

**SAY:**
> "Manufacturing data lives in Splunk — temperature, moisture, batch QC. Batch 1027: twenty-four deviations on coating machine COAT-01. That's the trigger."

**POINT AT:** **BATCH-1027** and **24**

**SHOW:** Switch back to **Streamlit** tab (http://localhost:8501)

**SAY:**
> "Plant managers don't live in Splunk. They work here — in PharmaOps."

---

### SCENE 3 — MULTI-AGENT (0:50 – 1:45) ⭐ MAIN DEMO

**SHOW:** **Multi-Agent** tab

**SAY:**
> "One click. Three AI agents: Detection finds the anomaly, Investigation pulls evidence from Splunk, QA Review validates FDA compliance."

**CLICK:** **🚀 Run Multi-Agent Pipeline**

**SAY while spinner runs (~1–2 min):**
> "Gemini reasons the root cause. GMP impact, CAPA, financial risk — all generated autonomously. No human investigator."

**SHOW:** When done — scroll through:
- Batch ID, Deviations, Impact metrics
- Agent analysis text below

**SAY:**
> "Full deviation investigation — batch ID, deviation count, QA decision, root cause — inside one app."

---

### SCENE 4 — REGULATORY (1:45 – 2:15)

**SHOW:** **Regulatory** tab

**CLICK:** **🚀 Generate Regulatory Report**

**SAY:**
> "Regulatory intelligence: GMP score, QMS risk, pharmacovigilance risk, ICH Q9 RPN — manual investigation takes six hours, we do it in two and a half minutes."

**SHOW:** Scroll to GMP / QMS / PV metrics and industry comparison numbers

**SAY:**
> "Five point two lakh saved per deviation. Twenty-one lakh plus in batch loss prevented with early detection."

---

### SCENE 5 — ASK AI (2:15 – 2:40)

**SHOW:** **Ask AI** tab

**TYPE:** `What batches failed and why?`

**CLICK:** **Ask**

**SAY:**
> "Plant managers ask in plain English. Gemini writes the Splunk query, live data comes back, AI answers with specific batch IDs and failure reasons."

**SHOW:** Answer + SPL query in expander

---

### SCENE 6 — CLOSE (2:40 – 3:00)

**SHOW:** Sidebar — MCP ✅ REST ✅ Gemini ✅ (or mention REST fallback)

**SAY:**
> "Built on Splunk MCP, AI Toolkit, and Google Gemini. PharmaOps Monitor — autonomous batch insurance for pharma. Code on GitHub: prakash023-hub/pharmaops-monitor. Thank you."

**SHOW:** GitHub URL in browser for 3 seconds

**STOP RECORDING**

---

## CHEAT SHEET (phone / second monitor)

```
0:00  Streamlit open — hook (money + 3 minutes)
0:25  Dashboard → Open Splunk → BATCH-1027 / 24 → back to Streamlit
0:50  Multi-Agent → Run button → wait → show results
1:45  Regulatory → Generate → show GMP/QMS/PV scores
2:15  Ask AI → "What batches failed and why?"
2:40  Sidebar status + GitHub + thank you
```

---

## IF SOMETHING BREAKS ON CAMERA

| Problem | Fix on video |
|---------|----------------|
| Multi-Agent slow | Keep talking — "AI is querying live Splunk data" |
| MCP yellow in sidebar | Say: "MCP with REST fallback — same live Splunk index" |
| Ask AI error | Skip to close — Scenes 1–4 are enough |
| Splunk won't open | Use Dashboard tab screenshot instead |
| Streamlit won't start | `open http://localhost:8501` manually |

---

## AFTER RECORDING

1. QuickTime → trim dead air
2. Upload YouTube (Unlisted OK)
3. Paste link in Devpost / Ignite64

---

## DO NOT DO ON VIDEO

- ❌ Terminal commands
- ❌ `python3 agent/pharma_agent.py --open-report`
- ❌ Separate HTML tabs popping open
- ❌ `./scripts/run_end_to_end.sh`

**Only Streamlit + 20 sec Splunk.**
