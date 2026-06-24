"""Trigger strategic agents for demo merchant via the live API."""
import asyncio
import urllib.request
import urllib.parse
import json

BASE = "http://localhost:8000/api/v1"

def post(path, body=None, token=None):
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

def get(path, token=None):
    req = urllib.request.Request(
        BASE + path,
        headers={"Authorization": f"Bearer {token}"} if token else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code


# Step 1: Login
print("Logging in as demo merchant...")
resp, status = post("/auth/login", {"identifier": "demo@sellermate.ai", "password": "Demo@123456"})
if status != 200:
    print(f"Login failed ({status}): {resp}")
    exit(1)

token = resp["data"]["tokens"]["access_token"]
merchant_name = resp["data"]["merchant"].get("business_name", "Demo")
print(f"Logged in: {merchant_name} (status {status})")

# Step 2: Run strategic agents
print("\nRunning strategic agents...")
resp2, status2 = post("/ai/strategic/run", {}, token)
if status2 == 200:
    result = resp2.get("data", resp2)
    trust = result.get("trust", {})
    fraud = result.get("fraud", {})
    print(f"Trust Score:      {trust.get('trust_score', 'N/A')} (confidence: {trust.get('confidence', 'N/A')})")
    print(f"Fraud Risk Score: {fraud.get('fraud_risk_score', 'N/A')}")
    flags = trust.get("risk_flags", [])
    alerts = fraud.get("alert_reasons", [])
    print(f"Risk Flags: {flags}")
    print(f"Fraud Alerts: {alerts}")
    print(f"\nInsights saved: {result.get('insights_saved', 'N/A')}")
else:
    print(f"Strategic agent run failed ({status2}): {json.dumps(resp2, indent=2, ensure_ascii=False)}")

# Step 3: Verify insights stored
print("\nVerifying stored insights...")
resp3, status3 = get("/ai/strategic/insights", token)
if status3 == 200:
    insights = resp3.get("data", [])
    print(f"Stored insights: {len(insights)}")
    for ins in insights:
        print(f"  [{ins.get('agent_name')}] score={ins.get('score')} at {ins.get('created_at', '')[:19]}")
else:
    print(f"Could not fetch insights ({status3}): {resp3}")
