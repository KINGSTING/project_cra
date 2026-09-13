import os
import json
import uuid
import asyncio
from http.server import BaseHTTPRequestHandler
import libsql_client
from dotenv import load_dotenv

load_dotenv()

async def get_assessments():
    url = os.getenv("TURSO_DATABASE_URL").replace("libsql://", "https://")
    auth_token = os.getenv("TURSO_AUTH_TOKEN")
    async with libsql_client.create_client(url, auth_token=auth_token) as client:
        result = await client.execute("SELECT assessment_id, agency_name, assessment_profile, status FROM assessments")
        return [
            {"assessment_id": row[0], "agency_name": row[1], "assessment_profile": row[2], "status": row[3]} 
            for row in result.rows
        ]

async def create_assessment(data):
    url = os.getenv("TURSO_DATABASE_URL").replace("libsql://", "https://")
    auth_token = os.getenv("TURSO_AUTH_TOKEN")
    new_id = f"ASSESSMENT#{uuid.uuid4().hex[:8]}"
    
    async with libsql_client.create_client(url, auth_token=auth_token) as client:
        await client.execute(
            "INSERT INTO assessments (assessment_id, agency_name, assessment_profile, status) VALUES (?, ?, ?, ?)",
            [new_id, data.get("agency_name", "Unknown Agency"), data.get("assessment_profile", "Default Profile"), "Draft"]
        )
    return new_id

class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        try:
            records = asyncio.run(get_assessments())
            self.wfile.write(json.dumps({"success": True, "data": records}).encode("utf-8"))
        except Exception as err:
            self.wfile.write(json.dumps({"success": False, "error": str(err)}).encode("utf-8"))

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data)
            
            new_id = asyncio.run(create_assessment(payload))
            self.wfile.write(json.dumps({"success": True, "assessment_id": new_id}).encode("utf-8"))
        except Exception as err:
            self.wfile.write(json.dumps({"success": False, "error": str(err)}).encode("utf-8"))