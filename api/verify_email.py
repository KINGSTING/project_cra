# api/verify_email.py
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import hmac
import hashlib
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from lib.db import get_db
from lib.auth import mint_session_jwt

TOKEN_SECRET    = os.environ.get("TOKEN_SECRET")
ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()]


def hash_token(t: str) -> str:
    return hmac.new(TOKEN_SECRET.encode(), t.encode(), hashlib.sha256).hexdigest()


def cors(origin: str) -> dict:
    return {
        "Access-Control-Allow-Origin": origin if origin in ALLOWED_ORIGINS else ALLOWED_ORIGINS[0],
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
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

        raw = (data.get("token") or "").strip()
        if not raw:
            return self._json(400, {"error": "missing_token"}, origin)

        try:
            db = get_db()

            row = db.execute(
                "SELECT id, email, agency, expires_at, used_at "
                "FROM email_verifications WHERE token_hash = ?",
                (hash_token(raw),),
            ).fetchone()

            if not row:
                return self._json(400, {"error": "invalid_token"}, origin)

            verif_id, email, agency, expires_at, used_at = row
            if used_at:
                return self._json(400, {"error": "already_used"}, origin)

            exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > exp:
                return self._json(400, {"error": "expired"}, origin)

            # Consume token
            db.execute(
                "UPDATE email_verifications SET used_at = datetime('now') WHERE id = ?",
                (verif_id,),
            )

            # Upsert user (create if new, else mark verified)
            db.execute(
                "INSERT INTO users (email, agency, role, verified) "
                "VALUES (?, ?, 'client', 1) "
                "ON CONFLICT(email) DO UPDATE SET "
                "  agency = excluded.agency, verified = 1",
                (email, agency),
            )
            db.commit()

            # Read the final user row so we can mint a JWT with fresh data
            user_row = db.execute(
                "SELECT id, email, agency, role, verified FROM users WHERE email = ?",
                (email,),
            ).fetchone()

            user = {
                "id":       user_row[0],
                "email":    user_row[1],
                "agency":   user_row[2],
                "role":     user_row[3],
                "verified": user_row[4],
            }

            token = mint_session_jwt(user)

            return self._json(200, {
                "status": "verified",
                "token":  token,
                "user":   user,
            }, origin)

        except Exception as e:
            print(f"[verify_email] error: {type(e).__name__}: {e}")
            traceback.print_exc()
            return self._json(500, {"error": "verify_failed"}, origin)