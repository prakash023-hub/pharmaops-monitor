# Grand Prize Submission Checklist

## Code (done)

- [x] Autonomous detect → investigate loop (`pharma_agent.py --autonomous`)
- [x] MCP-only chat with Gemini SPL generation (`mcp_chat_demo.py`)
- [x] FDA HTML deviation reports (`generate_report_html.py`)
- [x] Dashboard screenshots in `docs/dashboard/`
- [x] README quick-start guide
- [x] Architecture diagram in repo root
- [x] MIT license, requirements.txt, sample data
- [x] Video script (`docs/GRAND_PRIZE_VIDEO_SCRIPT.md`)
- [x] Devpost copy (`docs/DEVPOST_SUBMISSION.md`)

## You must do (2 items)

### 1. Record demo video (~2 hours)

Follow: [GRAND_PRIZE_VIDEO_SCRIPT.md](GRAND_PRIZE_VIDEO_SCRIPT.md)

```bash
export GEMINI_API_KEY=your_key
./run_demo.sh
# Record screen while running
```

Upload to YouTube (public/unlisted), under 3 minutes.

### 2. Submit on Devpost (~30 min)

1. Go to https://splunk.devpost.com/
2. Click "Enter Submission"
3. Copy text from [DEVPOST_SUBMISSION.md](DEVPOST_SUBMISSION.md)
4. Paste YouTube video URL
5. Paste GitHub URL: https://github.com/prakash023-hub/pharmaops-monitor
6. Select track: **Observability**
7. Submit before **Jun 15, 2026 9:30pm IST**

## Before recording — verify

```bash
cd ~/pharmaops-monitor
source .venv/bin/activate   # or: pip install -r requirements.txt
export GEMINI_API_KEY=your_key

# Splunk + MCP running:
python3 agent/pharma_agent.py --autonomous --open-report

# Works offline too (CSV fallback):
python3 agent/mcp_chat_demo.py "What batches failed?"
```

## Git push

```bash
git add -A
git commit -m "Grand Prize ready: autonomous agent, MCP chat, HTML reports, dashboard docs"
git push origin main
```
