# api/request_link.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import re
import traceback
from http.server import BaseHTTPRequestHandler
from lib.db import get_db
from lib.magic_link import create_and_send_link

FROM_EMAIL      = os.environ.get("FROM_EMAIL", "IMP-CRA Portal <onboarding@resend.dev>")
APP_URL         = os.environ.get("APP_URL", "http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
EMAIL_RE        = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def cors(origin: str) -> dict:
    return {
        "Access-Control-Allow-Origin": origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0],
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Max-Age": "86400",
        "Vary": "Origin",
    }


class handler(BaseHTTPRequestHandler):
    def _json(self, code, payload, origin=""):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for k, v in cors(origin).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        for k, v in cors(self.headers.get("Origin", "")).items():
            self.send_header(k, v)
        self.end_headers()

    def do_POST(self):
        origin = self.headers.get("Origin", "")
        try:
            n = int(self.headers.get("Content-Length") or 0)
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._json(400, {"error": "invalid_json"}, origin)

        email = (data.get("email") or "").strip().lower()
        if not EMAIL_RE.match(email) or len(email) > 254:
            return self._json(400, {"error": "invalid_email"}, origin)

        try:
            db = get_db()
            user = db.execute(
                "SELECT id, email, agency, role, verified FROM users WHERE email = ?",
                (email,),
            ).fetchone()

            # Privacy: always return "sent" so we don't leak whether email exists —
            # except rate limits, which the user would notice anyway.
            if not user or not user[4]:
                return self._json(200, {"status": "sent"}, origin)

            agency = user[2] or ""
            result = create_and_send_link(
                db, email, agency,
                app_url=APP_URL, from_email=FROM_EMAIL,
            )
            if "error" in result and result["error"] == "rate_limited":
                return self._json(429, result, origin)
            return self._json(200, {"status": "sent"}, origin)

        except Exception as e:
            print(f"[request_link] error: {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._json(500, {"error": "send_failed"}, origin)