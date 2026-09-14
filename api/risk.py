import os, json, uuid, asyncio
from http.server import BaseHTTPRequestHandler
from pathlib import Path
import libsql_client
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / '.env')
url = os.getenv("TURSO_DATABASE_URL", "").replace("libsql://", "https://")
token = os.getenv("TURSO_AUTH_TOKEN", "")

def calc_severity(l, i):
    score = l * i
    return "EXTREME" if score >= 12 else "HIGH" if score >= 8 else "MODERATE" if score >= 4 else "LOW"

async def get_risks(client_id):
    async with libsql_client.create_client(url, auth_token=token) as client:
        res = await client.execute("SELECT risk_id, client_id, process_area, risk_event, likelihood, impact, mitigation_control FROM risk_register WHERE client_id = ?", [client_id])
        out = []
        for r in res.rows:
            d = dict(zip(["risk_id", "client_id", "process_area", "risk_event", "likelihood", "impact", "mitigation_control"], r))
            d["score"] = d["likelihood"] * d["impact"]
            d["severity"] = calc_severity(d["likelihood"], d["impact"])
            out.append(d)
        return out

async def add_risk(data):
    rid = f"RISK#{uuid.uuid4().hex[:8]}"
    async with libsql_client.create_client(url, auth_token=token) as client:
        await client.execute(
            "INSERT INTO risk_register (risk_id, client_id, process_area, risk_event, likelihood, impact, mitigation_control) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [rid, data.get("client_id"), data.get("process_area"), data.get("risk_event"), int(data.get("likelihood", 1)), int(data.get("impact", 1)), data.get("mitigation_control", "")]
        )
    return rid

class handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        cid = "DOH_AGENCY"
        if "?" in self.path:
            for part in self.path.split("?")[1].split("&"):
                if part.startswith("client_id="): cid = part.split("=")[1]
        data = asyncio.run(get_risks(cid))
        self.wfile.write(json.dumps({"success": True, "data": data}).encode("utf-8"))

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        rid = asyncio.run(add_risk(body))
        self.wfile.write(json.dumps({"success": True, "risk_id": rid}).encode("utf-8"))