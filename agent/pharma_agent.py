from google import genai
import json, ssl, urllib.request, os
from datetime import datetime

SPLUNK_MCP_URL = "https://localhost:8089/services/mcp"
SPLUNK_TOKEN = open(os.path.expanduser("~/mcp_token.txt")).read().strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)


def splunk_search(spl):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    data = json.dumps({"jsonrpc":"2.0","method":"tools/call","params":{"name":"search","arguments":{"query":spl,"earliest_time":"-30d","latest_time":"now"}},"id":2}).encode()
    req = urllib.request.Request(SPLUNK_MCP_URL, data=data, headers={"Authorization":f"Bearer {SPLUNK_TOKEN}","Content-Type":"application/json"})
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=30)
        return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def investigate_batch(batch_id, anomaly_type, deviation):
    print(f"\n[AGENT] Investigating {batch_id} - {anomaly_type}")
    print("[AGENT] Step 1/4: Querying Splunk via MCP...")
    temp_data = splunk_search(f"search index=pharma_manufacturing source=temperature_logs.csv | stats avg(temperature_C) as avg_temp max(temperature_C) as max_temp by batch_id equipment_id | where batch_id=\"{batch_id}\"")
    downtime_data = splunk_search("search index=pharma_manufacturing source=equipment_downtime.csv | stats sum(downtime_minutes) as total_down by equipment_id | sort -total_down")
    batch_data = splunk_search(f"search index=pharma_manufacturing source=batch_summary.csv | where batch_id=\"{batch_id}\" | table batch_id product yield_pct deviation_count batch_status oee_score")
    print("[AGENT] Step 2/4: Reasoning via Gemini LLM...")
    prompt = f"""You are PharmaOps Agent, a GMP compliance investigator.

ANOMALY DETECTED:
- Batch ID: {batch_id}
- Anomaly: {anomaly_type}
- Deviation: {deviation} sigma
- Time: {datetime.now().isoformat()}

EVIDENCE FROM SPLUNK MCP:
Temp: {json.dumps(temp_data)}
Downtime: {json.dumps(downtime_data)}
Batch: {json.dumps(batch_data)}

Provide:
1. ROOT CAUSE (evidence-based)
2. GMP IMPACT: Critical/Major/Minor
3. CORRECTIVE ACTION (CAPA)
4. FINANCIAL IMPACT (INR lakhs)
5. CONFIDENCE SCORE
"""
    response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    report_text = response.text
    print("[AGENT] Step 3/4: Generating report...")
    report = {"report_id": f"DEV-{batch_id}-{datetime.now().strftime("%Y%m%d%H%M")}", "batch_id": batch_id, "anomaly_type": anomaly_type, "deviation_sigma": deviation, "timestamp": datetime.now().isoformat(), "agent_analysis": report_text}
    print("[AGENT] Step 4/4: Saving report...")
    open(f"agent/report_{batch_id}.json", "w").write(json.dumps(report, indent=2))
    print(f"[AGENT] Complete: {report['report_id']}")
    print("\n" + "="*60)
    print(report_text)
    print("="*60)
    return report

def run_demo():
    print("="*60)
    print("  PharmaOps Agent - Autonomous GMP Investigator")
    print("  Powered by Splunk MCP + Google Gemini")
    print("="*60)
    investigate_batch("BATCH-1011", "temperature_deviation", 3.2)
    investigate_batch("BATCH-1027", "temperature_deviation", 2.8)

if __name__ == "__main__":
    run_demo()
