#!/usr/bin/env python3
"""
Test deploy and run unified flow in Langflow.
"""

import gzip
import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:7860"

# 1. Auto login
print("1. Authenticating with Langflow...")
req = urllib.request.Request(f"{BASE_URL}/api/v1/auto_login")
with urllib.request.urlopen(req) as resp:
    login_data = json.loads(resp.read().decode())
    token = login_data["access_token"]
print("Auth token obtained.")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}

# 2. Load flow JSON
with open("flows/exports/socratica_unified.json") as f:
    flow_json = json.load(f)

flow_name = flow_json.get("name", "Socratica — All-in-One AI Assistant")
flow_id = flow_json.get("id", "fe99317c-abcc-4e05-85fd-e2d897fcbdf1")

# Check existing flows
print("2. Checking existing flows...")
req = urllib.request.Request(f"{BASE_URL}/api/v1/flows/", headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req) as resp:
    raw = resp.read()
    try:
        raw = gzip.decompress(raw)
    except Exception:
        pass
    flows = json.loads(raw.decode())

existing_flow = None
for f in flows:
    if f.get("id") == flow_id or f.get("name") == flow_name:
        existing_flow = f
        break

payload = {
    "name": flow_name,
    "description": "Unified flow for Socratica handling Guardrails, Q&A, Socratic tutoring, Evaluation, and Ingestion",
    "data": flow_json["data"],
    "endpoint_name": "socratica-unified",
}

if existing_flow:
    actual_flow_id = existing_flow["id"]
    print(f"Flow exists with ID {actual_flow_id}. Updating via PATCH...")
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/flows/{actual_flow_id}",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="PATCH",
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        print("Updated flow successfully!")
else:
    print("Creating new flow via POST /api/v1/flows/ ...")
    payload["id"] = flow_id
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/flows/",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        actual_flow_id = res["id"]
        print(f"Created flow successfully with ID {actual_flow_id}!")

# Update flow_id in JSON if different
flow_json["id"] = actual_flow_id
with open("flows/exports/socratica_unified.json", "w") as f:
    json.dump(flow_json, f, indent=2)

print(f"Unified Flow ID: {actual_flow_id}")

# 3. Test building/compiling the flow
print("3. Building / compiling the flow graph...")
build_url = f"{BASE_URL}/api/v1/build/{actual_flow_id}/flow"
req = urllib.request.Request(build_url, data=b"{}", headers=headers, method="POST")
try:
    with urllib.request.urlopen(req) as resp:
        print(f"Build endpoint responded with status: {resp.status}")
except urllib.error.HTTPError as e:
    err_body = e.read().decode()
    print(f"Build endpoint returned {e.code}: {err_body}")

# 4. Test running the flow
print("4. Testing flow execution via /api/v1/run/{flow_id} ...")
run_url = f"{BASE_URL}/api/v1/run/{actual_flow_id}"
run_payload = {
    "input_value": "Halo! Jelaskan secara singkat dalam 2 kalimat apa itu machine learning.",
    "input_type": "chat",
    "output_type": "chat",
    "tweaks": {
        "course_id": "test-course",
    }
}
req = urllib.request.Request(
    run_url,
    data=json.dumps(run_payload).encode("utf-8"),
    headers=headers,
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        run_res = json.loads(resp.read().decode())
        print("Run succeeded!")
        outputs = run_res.get("outputs", [])
        for out in outputs:
            for item in out.get("outputs", []):
                msg = item.get("results", {}).get("message", {})
                text = msg.get("text") or msg.get("data", {}).get("text")
                print("Generated Response:\n", text)
except urllib.error.HTTPError as e:
    err_body = e.read().decode()
    print(f"Run endpoint returned {e.code}: {err_body}")
except Exception as e:
    print(f"Run error: {type(e)} {e}")
