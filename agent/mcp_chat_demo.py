from google import genai
import json, ssl, urllib.request, urllib.parse, os

SPLUNK_URL = "https://localhost:8089"
SPLUNK_USER = "admin"
SPLUNK_PASS = os.getenv("SPLUNK_PASS", "Splunk@23")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def splunk_search(spl):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    creds = urllib.parse.urlencode({"username": SPLUNK_USER, "password": SPLUNK_PASS}).encode()
    login_req = urllib.request.Request(f"{SPLUNK_URL}/services/auth/login", data=creds)
    try:
        login_resp = urllib.request.urlopen(login_req, context=ctx, timeout=10)
        import xml.etree.ElementTree as ET
        tree = ET.parse(login_resp)
        token = tree.find(".//sessionKey").text
        search_data = urllib.parse.urlencode({"search": f"search {spl}", "output_mode": "json", "count": "20", "earliest_time": "0"}).encode()
        search_req = urllib.request.Request(f"{SPLUNK_URL}/services/search/jobs/export", data=search_data, headers={"Authorization": f"Splunk {token}"})
        search_resp = urllib.request.urlopen(search_req, context=ctx, timeout=30)
        results = []
        for line in search_resp:
            try:
                obj = json.loads(line)
                if "result" in obj:
                    results.append(obj["result"])
            except:
                pass
        return results[:10]
    except Exception as e:
        return {"error": str(e)}

def chat(question):
    print(f"\nPlant Manager: {question}")
    if "failed" in question.lower():
        data = splunk_search("index=pharma_manufacturing batch_status=FAIL | table batch_id product yield_pct deviation_count batch_status | head 10")
    elif "temperature" in question.lower():
        data = splunk_search("index=pharma_manufacturing status=DEVIATION | stats count by batch_id equipment_id | sort -count | head 5")
    elif "equipment" in question.lower():
        data = splunk_search("index=pharma_manufacturing downtime_minutes=* | stats sum(downtime_minutes) as total by equipment_id | sort -total")
    else:
        data = splunk_search("index=pharma_manufacturing | stats count by source")
    prompt = f"You are PharmaOps AI for pharma plant managers.\nQuestion: {question}\nReal Splunk Data: {json.dumps(data)}\nAnswer in 3-5 sentences citing specific batch IDs and numbers from the data."
    resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    print(f"PharmaOps Agent: {resp.text}")
    print("-"*60)

if __name__ == "__main__":
    print("="*60)
    print("PharmaOps MCP Chat - Natural Language Interface")
    print("="*60)
    chat("What batches failed and why?")
    chat("Which equipment had most downtime?")
    chat("Show temperature deviations by batch")
    chat("Generate GMP summary for QA team")
